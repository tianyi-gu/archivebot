from django.db import models

class PipelineState(models.Model):
    # Scraping state
    scraping_in_progress = models.BooleanField(default=False)
    scraping_completed_urls = models.JSONField(default=list)
    scraping_failed_urls = models.JSONField(default=list)
    scraping_total_urls = models.IntegerField(default=0)
    scraping_current_year = models.CharField(max_length=10, null=True, blank=True)
    
    # OCR state
    ocr_in_progress = models.BooleanField(default=False)
    ocr_completed_files = models.JSONField(default=list)
    ocr_failed_files = models.JSONField(default=list)
    ocr_total_files = models.IntegerField(default=0)
    ocr_current_file = models.CharField(max_length=255, null=True, blank=True)
    
    # Chunking state
    chunking_in_progress = models.BooleanField(default=False)
    chunking_completed_files = models.JSONField(default=list)
    chunking_failed_files = models.JSONField(default=list)
    chunking_total_files = models.IntegerField(default=0)
    chunking_current_file = models.CharField(max_length=255, null=True, blank=True)
    
    # Embedding state
    embedding_in_progress = models.BooleanField(default=False)
    embedding_completed_chunks = models.IntegerField(default=0)
    embedding_total_chunks = models.IntegerField(default=0)
    
    # Model state
    model_loaded = models.BooleanField(default=False)
    model_name = models.CharField(max_length=255, null=True, blank=True)
    
    # Singleton pattern - always use the same record
    @classmethod
    def get_instance(cls):
        instance, created = cls.objects.get_or_create(pk=1)
        return instance

class ChatMessage(models.Model):
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('bot', 'Bot')])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..." 