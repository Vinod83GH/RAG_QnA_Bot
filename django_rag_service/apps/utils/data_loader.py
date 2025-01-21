from abc import ABC, abstractmethod
# Loader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders import PyPDFLoader

# Step 1: Create an interface for document loaders
class DocumentLoader(ABC):
    def __init__(self, path):
        self.path = path

    @abstractmethod
    def load_doc(self):
        pass

# Step 2: Implement concrete classes for each document type
class DocxLoader(DocumentLoader):
    def load_doc(self):
        # Implement the logic to load a .docx file
         print(f"Loading .docx document from {self.path}")
         return Docx2txtLoader(self.path).load()

class PdfLoader(DocumentLoader):
    def load_doc(self):
        # Implement the logic to load a .pdf file
        print(f"Loading .pdf document from {self.path}")
        return PyPDFLoader(self.path).load()

# Step 3: Create a factory method
class DocumentLoaderFactory:
    @staticmethod
    def create_loader(path, file_extension):
        loaders = {
            '.docx': DocxLoader,
            '.pdf': PdfLoader
        }

        if file_extension not in loaders:
            raise Exception(f'Invalid document type. Allowed types are -- {loaders.keys()}')

        loader_class = loaders[file_extension]
        return loader_class(path)

# Usage
def load_document(path, file_extension='.docx'):
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
    loader = DocumentLoaderFactory.create_loader(path, file_extension)
    return loader.load_doc()