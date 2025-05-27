from django.contrib import admin
from .models import PipelineState, ChatMessage

@admin.register(PipelineState)
class PipelineStateAdmin(admin.ModelAdmin):
    list_display = ['id', 'model_loaded', 'model_name', 'scraping_in_progress', 'embedding_in_progress']
    readonly_fields = ['id']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['message_preview', 'response_preview', 'is_user', 'timestamp']
    list_filter = ['is_user', 'timestamp']
    readonly_fields = ['timestamp']
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
    
    def response_preview(self, obj):
        return obj.response[:50] + "..." if len(obj.response) > 50 else obj.response
    response_preview.short_description = 'Response' 