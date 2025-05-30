# ArchiveBot

Archivebot is a Django-based RAG (Retrieval-Augmented Generation) system that enables intuitive, conversational access to archival material. Present-day researchers interested in working with historical documents are forced to menially sift through thousands of pages of documents. Despite digitization and search functionality, this process is not only time-consuming, but also error-prone. 

This project aims to alleviate this issue by allowing users to query the archive through natural language, and receive a summary of the most relevant information from the archive.

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

4. Access the application at http://127.0.0.1:8000/

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

## Known Issues
- Occasionally requires resetting embeddings and loading model after refreshing to run correctly.
- Progress updating and sometimes hangs on retrieving pdfs
- Excessive amounts of time when loading (might be unavoidable but maybe a way to speed things up)
- Database resetting/not resetting when it should/shouldn't
- Processing years outside of what is user-specified

## To-dos and Future Steps
- Filtering based on article type (excluding Eighth Page articles, etc.)
- Linking to view original article PDF
- UI testing for level of parameters able to be set (currently the panel is more like an admin panel, users probably wouldn't actually see anything but the chat)
- Additional weighting based on recency of source material

Developed in the Computer Science 600 Research and Development Class at Phillips Academy. 
