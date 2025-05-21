from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/status', views.get_status, name='status'),
    path('api/scrape', views.start_scraping, name='scrape'),
    path('api/ocr', views.start_ocr, name='ocr'),
    path('api/chunk', views.start_chunking, name='chunk'),
    path('api/embed', views.start_embedding, name='embed'),
    path('api/load_model', views.load_model_view, name='load_model'),
    path('api/query', views.query, name='query'),
    path('api/chat_history', views.get_chat_history, name='chat_history'),
] 