from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Sets up the ArchiveBot application by running migrations and creating necessary directories'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up ArchiveBot application...'))
        
        # Run migrations
        self.stdout.write('Running migrations...')
        call_command('makemigrations', 'rag_app')
        call_command('migrate')
        
        # Create necessary directories
        directories = [
            settings.DATA_DIR,
            settings.RAW_CORPUS_DIR,
            settings.TEXT_CORPUS_DIR,
            settings.CHUNKED_CORPUS_DIR,
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            self.stdout.write(f'Created directory: {directory}')
        
        # Create static directories
        static_dirs = [
            settings.BASE_DIR / "rag_app" / "static" / "rag_app" / "css",
            settings.BASE_DIR / "rag_app" / "static" / "rag_app" / "js",
        ]
        
        for directory in static_dirs:
            os.makedirs(directory, exist_ok=True)
            self.stdout.write(f'Created static directory: {directory}')
        
        self.stdout.write(self.style.SUCCESS('Setup complete!')) 