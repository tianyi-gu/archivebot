from django.apps import AppConfig

class RagAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rag_app'
    
    def ready(self):
        # Reset pipeline state on server startup
        try:
            from .models import PipelineState
            state = PipelineState.get_instance()
            state.scraping_in_progress = False
            state.ocr_in_progress = False
            state.chunking_in_progress = False
            state.embedding_in_progress = False
            state.save()
            print("Pipeline state reset on startup")
        except Exception as e:
            print(f"Could not reset pipeline state: {e}") 