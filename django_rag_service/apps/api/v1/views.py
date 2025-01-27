import pandas as pd

from adrf.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser


import psycopg2
import openai


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from apps.ai_core.rag import DocumentManager
from apps.ai_core.prompts.openai_tools_prompt import generate_prompt

@csrf_exempt
@api_view()
async def health_check(request) -> Response:
    return Response(status=status.HTTP_200_OK, data='Ready for connection!!')


@csrf_exempt
@api_view(["POST"])
async def health_check_post(request) -> Response:
    return Response(status=status.HTTP_200_OK, data='POST is ready for connection!!')


@csrf_exempt
@api_view(["POST"])
async def check_db_connection(request) -> Response:
    # Database config
    database_config = {
        "host": settings.DATABASES['default']['HOST'],
        "database": settings.DATABASES['default']['NAME'],
        "user": settings.DATABASES['default']['USER'],
        "password": settings.DATABASES['default']['PASSWORD'],
        "port": settings.DATABASES['default']['PORT']
    }

    # Call to the DocumentManager
    doc_manager = DocumentManager(
        model_name= "qna_table",
        api_key=settings.OPENAI_API_KEY,
        **database_config
    )

    # doc_manager.create_vector_store_from_document(document_file_path, **{
    #     "collection_name": "qna_text_str",
    #     "meta_data": ""
    # })

    # return doc_manager.get_pg_vector_connection_string()
    return Response(status=status.HTTP_200_OK, data=doc_manager.get_pg_vector_connection_string())


# CSRF exempt view for handling file uploads
@csrf_exempt
@api_view(["POST"])
def upload_file(request) -> Response:
    parser_classes = [MultiPartParser, FormParser]

    model_name = request.data.get('model_name') # LLM Model used for storage - text-embedding-ada-002
    collection_name = request.data.get('collection_name') # Table name
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    file_storage = FileSystemStorage()
    filename = file_storage.save(file.name, file)
    file_path = file_storage.path(filename)

    # Database config
    database_config = {
        "host": settings.DATABASES['default']['HOST'],
        "database": settings.DATABASES['default']['NAME'],
        "user": settings.DATABASES['default']['USER'],
        "password": settings.DATABASES['default']['PASSWORD'],
        "port": settings.DATABASES['default']['PORT']
    }

    # Call to the DocumentManager
    doc_manager = DocumentManager(
        model_name= model_name,
        api_key=settings.OPENAI_API_KEY,
        **database_config
    )

    doc_manager.create_vector_store_from_document(file_path, **{
        "collection_name": collection_name
    })

    return Response(status=status.HTTP_200_OK, data=f"File {filename}, successfully stored into vector store")


# CSRF exempt view for handling file uploads
@csrf_exempt
@api_view(["POST"])
def Question_n_Answer_Bot(request) -> Response:
    '''
    open AI Models used in this API
    gpt-4o-mini
    text-embedding-ada-002
    gpt-3.5-turbo-instruct
    '''
    search_query = request.data.get('query_text')
    collection_name = request.data.get('collection_name')

    # Database config
    database_config = {
        "host": settings.DATABASES['default']['HOST'],
        "database": settings.DATABASES['default']['NAME'],
        "user": settings.DATABASES['default']['USER'],
        "password": settings.DATABASES['default']['PASSWORD'],
        "port": settings.DATABASES['default']['PORT']
    }

    # Call to the DocumentManager
    doc_management_obj = DocumentManager(
        model_name=  settings.MODEL_NAME,
        api_key=settings.OPENAI_API_KEY,
        **database_config
    )

    relevant_chunks = doc_management_obj.similarity_search(collection_name, search_query)

    answer = doc_management_obj.generate_answer(search_query, relevant_chunks)

    print('answer based on relevant_chunks--> ', answer)

    print('relevant_chunks--> ', relevant_chunks)

        # Step 3: Provide document links if needed
    source = [{"source": chunk.metadata["source"]} for chunk in relevant_chunks]
    
    reponse_data =  {"answer": answer, "source": source}

    return Response(status=status.HTTP_200_OK, data=reponse_data)


# async def upload_documents(request) -> Response:
#     # save_document_and_chunks()


# # Define serializers
# class DocumentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Document
#         fields = ['id', 'title', 'content', 'file_path']

# class DocumentChunkSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DocumentChunk
#         fields = ['id', 'document', 'chunk_index', 'content']

    # Function to save document and chunks using DRF ORM

@csrf_exempt
@api_view(["POST"])
async def query_documents(request) -> Response:

    # Database config
    database_config = {
        "host": settings.DATABASES['default']['HOST'],
        "database": settings.DATABASES['default']['NAME'],
        "user": settings.DATABASES['default']['USER'],
        "password": settings.DATABASES['default']['PASSWORD'],
        "port": settings.DATABASES['default']['PORT']
    }

    search_query = request.data.get('query')

    # Call to the DocumentManager
    doc_management_obj = DocumentManager(
        model_name=  settings.MODEL_NAME,
        api_key=settings.OPENAI_API_KEY,
        **database_config
    )
    
    # Step 1: Search for relevant chunks
    relevant_chunks = doc_management_obj.search_relevant_chunks(search_query)
    
    # Step 2: Generate a concise answer
    answer = doc_management_obj.generate_answer(search_query, relevant_chunks)
    
    # Step 3: Provide document links if needed
    links = [{"title": chunk.metadata["title"], "link": chunk.metadata["file_path"]} for chunk in relevant_chunks]
    
    response_data =  {"answer": answer, "links": links}

    return Response(status=status.HTTP_200_OK, data=response_data)
