from django.contrib import admin
from .models import PipelineState, ChatMessage

@admin.register(PipelineState)
class PipelineStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'scraping_in_progress', 'ocr_in_progress', 'chunking_in_progress', 
                    'embedding_in_progress', 'model_loaded', 'model_name')
    readonly_fields = ('id',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'content', 'timestamp')
    list_filter = ('sender', 'timestamp')
    search_fields = ('content',) 