import os
import tiktoken

# Loader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import PyPDFLoader

# Splitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
# Vector database
from langchain_community.vectorstores.pgvector import PGVector
# Embedding
from langchain_openai import OpenAIEmbeddings
# Langchain Document
from langchain_core.documents import Document

from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from apps.utils.data_loader import load_document


from django.db import transaction
# from apps.api.models import Document, DocumentChunk

# from PyPDF2 import PdfReader


from django.conf import settings


class DocumentManager():
    """ Class to Manage the Document using RAG architecture which involves below operations
        - Load document - Split doc - Index doc - Store - Search doc and other related operations
    """
    def __init__(self, model_name, api_key, **kwargs):
        """ Init class with the required params
            Params:
                model_name
                api_key
                kwargs:
                    host: required
                    database: required
                    password: required
                    driver: optional - default - psycopg2
                    port: optional - default - 5432
        """
        self.model_name = model_name
        self.api_key = api_key
        self.host = kwargs["host"]
        self.database = kwargs['database']
        self.user = kwargs['user']
        self.password = kwargs['password']
        self.db_driver = kwargs.get('driver', "psycopg2")
        self.port = kwargs.get('port', 5432)
        self.allowed_doc_types = {
            '.docx': Docx2txtLoader,
            '.pdf': PyPDFLoader
        }

        # Get connection string which will be used to do any DB operations
        self.connection_string = self.get_pg_vector_connection_string()

    def get_pg_vector_connection_string(self):
        """ Method to get the pg_vector connection string 
            Returns:
                Connection string
        """
        connection_string = PGVector.connection_string_from_db_params(
            driver=self.db_driver,
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )

        return connection_string

    def get_embedding(self, embedding_type=None):
        """ Get the embedding to be used
            embedding_type - Type of embedding to be used.
                - Default - openai (OpenAIEmbeddings)
        """
        print('settings.OPENAI_ENDPOINT --> ',settings.OPENAI_ENDPOINT)
        print('self.api_key --> ',self.api_key)
        if not embedding_type:
            # If not specified then use OpenAI
            return OpenAIEmbeddings(
                openai_api_key=self.api_key,
                openai_api_base=settings.OPENAI_ENDPOINT
            )
    
    # import os
    # import psycopg2
    # from langchain.text_splitter import RecursiveCharacterTextSplitter
    # from langchain.embeddings import OpenAIEmbeddings
    # from langchain.vectorstores.pgvector import PGVector

    # def load_document_into_vectorstore(file_path):
    #     # Parse the file based on type (PDF, DOCX, TXT)
    #     # Use appropriate libraries like PyPDF2, python-docx, etc.
    #     content = extract_text(file_path)  # Implement this based on file type
    #     return content

    def load_document(self, path, file_extension='.docx'):
        """
        Load a document from the specified path.

        Args:
            path (str): The path to the document file.
            file_extension (str, optional): The extension type of the document. Defaults to '.docx'.

        Raises:
            Exception: If the document type is not allowed.

        Returns:
            str: The loaded document content.
        """

        self.allowed_doc_types = {
            '.docx': Docx2txtLoader,
            '.pdf': PyPDFLoader
        }

        allowed_doc_types = self.allowed_doc_types.keys()

        if file_extension not in allowed_doc_types:
            raise Exception(f'Invalid document type. Allowed types are -- {allowed_doc_types}')

        doc_loader_type = self.allowed_doc_types[file_extension]
        docx_loader = doc_loader_type(path)

        return docx_loader.load()

    def split_document_into_chunks(self, document_data, chunk_size=None, chunk_overlap=None):
        """ Method to split the documents into the chunks of defined size
            Params:
                chunk_size - split the doc into chunks with this as the max size 
                chunk_overlap specifies the number of overlapping tokens between consecutive chunks.
        """
        # Default chunk size
        if not chunk_size:
            chunk_size = 500
        # Default chunk overlap number
        if not chunk_overlap:
            chunk_overlap = 50

        encoding = tiktoken.encoding_for_model(self.model_name)
        end_line_to_split = "--END--"
        start_line_to_split = "--BEGIN--"

        docs_to_split_further_with_meta = {}
        document_chunks = []

        # Custom Chunk logic :: Check for text between the start and end line seperator
        # If we found, then dont chunk it further, If not found then chunk it further
        for each_doc in document_data:

            docs_to_split_further = ""
            docss_to_not_split_further = ""

            # Fetch the content in complete page
            doc_content = each_doc.page_content

            # Fetch the metadata
            doc_metadata = each_doc.metadata
            # get the source_path from meta
            doc_source_path = doc_metadata['source']

            # List of dcos after it got split by the end line
            doc_list_splitted_by_end_line = doc_content.split(end_line_to_split)

            for each_doc_chunk in doc_list_splitted_by_end_line:
                # Split the doc by the start line
                doc_list_splitted_by_start_line = each_doc_chunk.split(start_line_to_split)
                if len(doc_list_splitted_by_start_line) == 2:
                    # If there are more than one chunks then print them
                    docss_to_not_split_further=doc_list_splitted_by_start_line[1]

                    # Grop by doc meta for those document which we dont have to split further
                    if docss_to_not_split_further:
                        # Consolidate all the chunks which we should not split further
                        document_chunks.append(Document(
                            page_content=docss_to_not_split_further,
                            metadata=doc_metadata
                        ))

                    if  doc_list_splitted_by_start_line[0].strip() != '':
                        # Append the first chunk to the docs_to_split_further
                        docs_to_split_further += (doc_list_splitted_by_start_line[0] + "\n")

                elif len(doc_list_splitted_by_start_line) == 1:
                    # If there is only one chunk
                    if  doc_list_splitted_by_start_line[0].strip() != '':
                        docs_to_split_further += (doc_list_splitted_by_start_line[0] + "\n")
                else:
                    # There are more than 2 chunks, which means more than one start line
                    # This should not happen
                    print("Erorr!! Delimiter not ended!!!!")
                    raise Exception("Delimiter not ended!!")

            if docs_to_split_further:
                # Grop by doc meta for those document which we have to split further
                if doc_source_path not in docs_to_split_further_with_meta:
                    docs_to_split_further_with_meta[doc_source_path] = {
                        "page_content": docs_to_split_further,
                        "metadata": doc_metadata
                    }
                else:
                    docs_to_split_further_with_meta[doc_source_path]["page_content"] += docs_to_split_further

        # Recursivly split the doc
        # from_tiktoken_encoder - it will ensure that the chunk size will not be grater than than the size allowed by llm
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            model_name=self.model_name,
            encoding_name=encoding
        )
        print('docs_to_split_further_with_meta -->', docs_to_split_further_with_meta)
        for key, doc_values in docs_to_split_further_with_meta.items():
            if doc_values["page_content"]:
                document_data = Document(
                    page_content=doc_values["page_content"],
                    metadata=doc_values["metadata"]
                )

                # Split the doc using above text splitter
                document_chunks += text_splitter.split_documents([document_data])

        return document_chunks

    def create_vector_store(self, embedding_func,  document_chunks, collection_name):
        """ Method to create vector from doc chunks using embedding func & store in vectore DB
            Params:
                embedding_func - embedding function to use for embedding
                document_chunks - list of splitted document into smaller chunks
                collection_name - name of collection in Vector db to store the data
        """
        # Delete existing collection and create new from the document provided
        pg_vector_db = PGVector.from_documents(
            embedding=embedding_func,
            documents=document_chunks,
            collection_name=collection_name,
            connection_string=self.connection_string,
            pre_delete_collection=False,
        )

        return pg_vector_db

    def add_update_vector_store(self, embedding_func,  document_chunks, collection_name):
        """ Method to create vector from doc chunks using embedding func & store in vectore DB
            Params:
                embedding_func - embedding function to use for embedding
                document_chunks - list of splitted document into smaller chunks
                collection_name - name of collection in Vector db to store the data
        """
        # Delete existing collection and create new from the document provided
        pg_vector_db = PGVector.add_documents(
            embedding=embedding_func,
            documents=document_chunks,
            collection_name=collection_name,
            connection_string=self.connection_string,
            pre_delete_collection=True,
        )

        return pg_vector_db
  
    def get_retriever(self, vector_db, type, **kwargs):
        """
        Returns a retriever object based on the specified type.

        Parameters:
            vector_db (VectorDB): The vector database used for retrieval.
            type (str): The type of retriever to create.
            **kwargs: Additional keyword arguments to pass to the retriever constructor.

        Returns:
            Retriever: A retriever object based on the specified type.

        """
        # Use vector store-backed retriever as a default retriever
        if not type:

            # Check if any seacrh kwargs are provided
            search_kwargs = kwargs.get('search_kwargs', {})

            if search_kwargs:
                print("Filters applied!")
                retriever = vector_db.as_retriever(search_kwargs=kwargs['search_kwargs'])
            else:
                print("No filters applied!")
                retriever = vector_db.as_retriever(**kwargs)

            return retriever

    def create_vector_store_from_document(self, file_path, **kwargs):
        """ Method to create vector store from a document 
            This involves below steps:
                1. Load document
                2. split document into small chunks
                3. embed the chunks
                4. store embedded chinks into vector db
            Params:
                file_path - path to doc/file
                kwargs - additional keyword args
                    - collection_name (Required) - name of the collection to be stored in vector database
            Returns True on success
        """
        collection_name = kwargs['collection_name']
        # meta_data = kwargs['meta_data']

        filename, file_extension = os.path.splitext(file_path)

        # load document
        # document = self.load_document(file_path, file_extension)
        document = load_document(file_path, file_extension)

        # get document embedding to store with
        embedding_function = self.get_embedding()

        # split the loaded document into small chunks
        doc_chunks = self.split_document_into_chunks(document)

        # create vectore store into collection
        return self.create_vector_store(embedding_function, doc_chunks, collection_name)


    def chunk_document(self, content):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Adjust chunk size as needed
            chunk_overlap=50  # Small overlap to preserve context
        )
        chunks = text_splitter.split_text(content)
        return chunks
    
    def extract_pdf(self, filepath):
        full_content =''
        # Read and extract text from the uploaded PDF
        # reader = PdfReader(filepath)
        for page in reader.pages:
            full_content += page.extract_text() + "\n"

        print('Extracted full pdf content ->> ', full_content)

        return full_content

    def save_document_and_chunks(self, filename, document_content, file_path, doc_chunks):
        try:
            # new_document_id = 0
            # with transaction.atomic():
            #     # Create and save the document
            #     document = Document.objects.create(
            #         title=filename,
            #         content=document_content,
            #         file_path=file_path
            #     )
            #     new_document_id = document.id
            #     print(f'New document created with ID: {new_document_id}')

                # # Create and save document chunks
                # for index, chunk in enumerate(doc_chunks):
                #     document_chunk = DocumentChunk.objects.create(
                #         document=document,
                #         chunk_index=index,
                #         content=chunk
                #     )
                #     print(f'New chunk created with ID: {document_chunk.id}')

                print('Final DB commit on document and chunks creation')

        except Exception as e:
            print(f'Error occurred: {e}')
            raise
        
        # return new_document_id


    def Load_document_chunks_separately(self, file_path):
        """ Method to create vector store from a document 
            This involves below steps:
                1. Load document
                2. split document into small chunks
                3. embed the chunks
                4. store embedded chinks into vector db
            Params:
                file_path - path to doc/file
                kwargs - additional keyword args
                    - collection_name (Required) - name of the collection to be stored in vector database
            Returns True on success
        """
        # collection_name = kwargs['collection_name']
        # db_conn = kwargs['db_conn']
        # meta_data = kwargs['meta_data']

        filename, file_extension = os.path.splitext(file_path)

        # load document
        # document = self.load_document(file_path, file_extension)
        doc_content = self.extract_pdf(file_path)
        # # After document got loaded, update the metadata
        # for each_chunk in document:
        #     # If loaded from S3 then put the s3 path in meta, else it will auto take the local file path in meta
        #     if settings.POLICY_DOCUMENT_SOURCE == 'S3':
        #         each_chunk.metadata['source'] = file_path

        #     each_chunk.metadata.update(meta_data)
        # specify type of embedding function to be used
        # embedding_function = self.get_embedding()
        # split the loaded document into small chunks
        # print('Loaded document --> ', document[0].page_content)
        # doc_chunks = self.chunk_document(document[0].page_content)

        # db_conn = psycopg2.connect("dbname=postgres user=postgres password=postgres host=pgvector_db port=5432")

        # with db_conn.cursor() as cursor:
        #     # Insert document metadata
        #     cursor.execute(
        #         "INSERT INTO documents (title, content, file_path) VALUES (%s, %s, %s) RETURNING id",
        #         (filename, document[0].page_content, file_path)
        #     )
        #     document_id = cursor.fetchone()[0]
        #     print('new document_id created -->', document_id)
            
        #     # Insert chunks
        #     # embeddings = OpenAIEmbeddings()
        #     for index, chunk in enumerate(doc_chunks):
        #         # embedding = embeddings.embed_text(chunk)
        #         cursor.execute(
        #             "INSERT INTO document_chunks (document_id, chunk_index, content) VALUES (%s, %s, %s)",
        #             (document_id, index, chunk)
        #         )
        #         chunk_id = cursor.fetchone()[0]
        #         print('new chunk_id created -->', chunk_id)
        #         # cursor.execute(
        #         #     "UPDATE document_chunks SET embedding = %s WHERE id = %s",
        #         #     (embedding, chunk_id)
        #         # )
        # db_conn.commit()
        # print('Final DB commit on document and chunks creation', chunk_id)

        chunks = self.chunk_document(doc_content)

        new_document_id = self.save_document_and_chunks(filename, doc_content, file_path, chunks)
        
        # Finally update Embeddings for each chunks
        self.update_embeddings_for_document(new_document_id)

        print('Document store successfully !')

        # return chunk_id
    
    def update_embeddings_for_document(self, document_id):

        embeddings = OpenAIEmbeddings()
        try:
            with transaction.atomic():
                chunks = DocumentChunk.objects.filter(document__id=document_id)
                print('Chunks fetched -->', chunks)

                for chunk in chunks:
                    embedding = embeddings.embed_text(chunk.content)
                    chunk.embedding = embedding
                    chunk.save()
                    print(f'Chunk Id - {chunk.id} | document Id - {document_id} : updated with embedding')

                print('Final commit on embedding update')
        except Exception as e:
            print(f'Error occurred in update enbeddings for document id - {document_id}: {e}')
            raise
        

        # embeddings = OpenAIEmbeddings()
        # with db_conn.cursor() as cursor:
        #     cursor.execute("SELECT id, content FROM document_chunks")
        #     chunks = cursor.fetchall()
        #     print('chunks fecthed --> ', chunks)
        #     for chunk_id, chunk_content in chunks:
        #         embedding = embeddings.embed_text(chunk_content)
        #         cursor.execute(
        #             "UPDATE document_chunks SET embedding = %s WHERE id = %s",
        #             (embedding, chunk_id)
        #         )
        #         print('chunks updated with embedding')
        
        # db_conn.commit()
        # print('Final commit on embedding update')

    def generate_answer(self, question, relevant_chunks):
        llm = OpenAI()
        qa_chain = load_qa_chain(llm, chain_type="stuff")  # 'stuff' is a basic QA chain
        answer = qa_chain.run(input_documents=relevant_chunks, question=question)
        return answer
    
    # from langchain.vectorstores.pgvector import PGVector

    def search_relevant_chunks(self, question):
        embeddings = OpenAIEmbeddings()
        # query_embedding = embeddings.embed_query(question)
        vectorstore = PGVector(
            postgres_connection_string=self.connection_string,
            embeddings=embeddings,
            table_name="document_chunks"
        )
        results = vectorstore.similarity_search(question, top_k=5)
        return results

    
    def get_existing_vector_store(self, collection_name):
        """
        Retrieves the existing PGVector object for the specified collection.

        Parameters:
        collection_name (str): The name of the collection.

        Returns:
        PGVector: The existing PGVector object for the specified collection.
        """
        # specify type of embedding used to embed the doc earlier
        embedding_func = self.get_embedding()
        # return existing PGVector
        return PGVector(
            collection_name=collection_name,
            connection_string=self.connection_string,
            embedding_function=embedding_func,
        )

    def similarity_search_with_score(self, collection_name, query):
        """ Function for similarity search with score 
            Input:
                collection_name - Name of the collection where we have to search
                query - Query to be searched
            Output: searches the doc and returns similarity chunks with score
        """
        vector_db = self.get_existing_vector_store(collection_name)
        return vector_db.similarity_search_with_score(query)
    
    def similarity_search_Old(self, collection_name, query):
        """ Function for similarity search with score 
            Input:
                collection_name - Name of the collection where we have to search
                query - Query to be searched
            Output: searches the doc and returns similarity chunks with score
        """
        vector_db = self.get_existing_vector_store(collection_name)
        return vector_db.similarity_search(query)

    # from langchain.vectorstores.pgvector import PGVector

    
    def similarity_search(self, collection_name, query):
        """ Function for similarity search with score 
            Input:
                collection_name - Name of the collection where we have to search
                query - Query to be searched
            Output: searches the doc and returns similarity chunks with score
        """
        vector_db = self.get_existing_vector_store(collection_name)
        return vector_db.similarity_search(query, top_k=5)

    def search_relevent_document(self, collection_name, query, **kwargs):
        """
        Search for relevant documents in the specified collection using the given query.

        Args:
            collection_name (str): The name of the collection to search in.
            query (str): The query string to search for.
            **kwargs: Additional keyword arguments.

        Returns:
            list: A list of relevant documents matching the query.
        """
        vector_db = self.get_existing_vector_store(collection_name)
        retriever = self.get_retriever(vector_db, None, **kwargs)

        relevent_docs = retriever.get_relevant_documents(query)

        if not relevent_docs:
            return None
        else:
            return relevent_docs


    def add_document(self, file_path, collection_name, meta_data):
        """ Function to add the chunked document to the existing store
            This function can be only used to add new details to the existing vector collection (Append)
            But can not be used to update the existing data or to create newly
            file_path - path to doc/file to read and load
            documents_chunks - list of doc chunks of type [Document] to be added
        """
        # Extract file name & type from the full path
        filename, file_extension = os.path.splitext(file_path)

        # load document
        document = self.load_document(file_path, file_extension)
        # After document got loaded, update the metadata

        # for each_chunk in document:
        #     if settings.POLICY_DOCUMENT_SOURCE == 'S3':
        #         each_chunk.metadata['source'] = file_path

        #     each_chunk.metadata.update(meta_data)

        # split the loaded document into small chunks
        doc_chunks = self.split_document_into_chunks(document)
        # Get existing vector store using the collection name
        vector_store = self.get_existing_vector_store(collection_name)
        # Add document chunks [List] into the existing vector store
        return vector_store.add_documents(doc_chunks)
