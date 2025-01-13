import pandas as pd

from adrf.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
from langchain_openai import ChatOpenAI
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

    model_name = request.data.get('model_name')
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
        "collection_name": "QnA_doc_store"
    })

    return Response(status=status.HTTP_200_OK, data="successfully store documents into vector store")


# CSRF exempt view for handling file uploads
@csrf_exempt
@api_view(["POST"])
def Question_n_Answer_Bot(request) -> Response:
    search_query = request.data.get('query_text')
    model_name = ""

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

    kwargs = {}
    results = doc_management_obj.search_relevent_document(
        collection_name='QnA_doc_store',
        query=search_query,
        **kwargs
    )

    refined_contextual_prompt = generate_prompt(search_query,results)

    openai.api_key = settings.OPENAI_API_KEY
    gpt_response = openai.Completion.create(
        model=settings.MODEL_NAME,
        prompt=refined_contextual_prompt,
        max_tokens=200,
        temperature=0
    )
    refined_answer = gpt_response['choices'][0]['text'].strip()

    return Response(status=status.HTTP_200_OK, data=refined_answer)
