from django.urls import include, path, re_path
from .views import health_check, health_check_post, check_db_connection,upload_file, Question_n_Answer_Bot

urlpatterns = [
    re_path(r'health-check', health_check_post, name="health_check_post"),
    re_path(r'check-db-connection', check_db_connection,name="check_db_connection"),
    re_path(r'upload-document', upload_file,name="upload_file"),
    re_path(r'question-answer-bot', Question_n_Answer_Bot,name="Question_n_Answer_Bot"),
]
