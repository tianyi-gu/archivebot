from django.core.management.base import BaseCommand
from django.core.management import call_command
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
        dirs = ['raw_corpus', 'text_corpus', 'chunked_corpus']
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
            self.stdout.write(f'Created directory: {directory}')
        
        self.stdout.write(self.style.SUCCESS('Setup complete!')) 