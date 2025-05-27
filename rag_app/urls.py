from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/status', views.status, name='status'),
    path('api/scrape', views.scrape, name='scrape'),
    path('api/ocr', views.ocr, name='ocr'),
    path('api/chunk', views.chunk, name='chunk'),
    path('api/embed', views.embed, name='embed'),
    path('api/load_model', views.load_model, name='load_model'),
    path('api/query', views.query, name='query'),
    path('api/chat_history', views.chat_history, name='chat_history'),
    path('api/reset_state', views.reset_state, name='reset_state'),
] 