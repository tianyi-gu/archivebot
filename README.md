# ArchiveBot

This project is a Django-based RAG (Retrieval-Augmented Generation) system that enables intuitive, conversational access to archived materials from the Oliver Wendell Holmes library.

## Setup Instructions

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up the Django app:
   ```
   python manage.py setup_app
   ```

3. Run the development server:
   ```
   python manage.py runserver
   ```

4. Access the application at http://localhost:8000

## Features

- Web scraping of archive materials
- OCR processing of PDF documents
- Text chunking (semantic or fixed-size)
- Embedding generation
- Interactive chat interface with RAG capabilities

## Project Structure

- `rag_app/`: The main Django application
  - `models.py`: Database models for pipeline state and chat history
  - `views.py`: API endpoints and view functions
  - `pipeline.py`: Core pipeline functionality
  - `urls.py`: URL routing
  - `templates/`: HTML templates

## Usage

1. Start by scraping archive materials for specific years
2. Process the downloaded PDFs with OCR
3. Chunk the extracted text
4. Generate embeddings for the chunks
5. Load a language model
6. Chat with the system to query the archived materials

This project aims to develop an AI-powered retrieval-augmented generation (RAG) system that  enables intuitive, conversational access to archived materials from the Oliver Wendell Holmes  library. This would be available to students, librarians, faculty, and any others who are curious about  engaging with the school's history in an accessible manner. This project will enable users to leverage  natural language search, in order for users to be able to retrieve summaries and context-rich  information from historical documents.

Developed in the Computer Science 600 Research and Development Class at Phillips Academy. 