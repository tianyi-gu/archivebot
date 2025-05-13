# ArchiveBot

Tianyi Gu for CSC600

This document outlines the process of building ArchiveBot, a retrieval-augmented generation (RAG) system that enables intuitive, conversational access to archived materials from the Oliver Wendell Holmes library. It aims to serve as a way to understand the behind-the-scenes working to enable others to contribute to this project or take inspiration from it.

## Overview

The system processes PDF documents through several stages:
1. Web scraping and downloading PDFs
2. PDF compression for efficient storage
3. OCR (Optical Character Recognition) to extract text
4. Text chunking for better retrieval
5. Embedding generation for semantic search
6. Vector search capabilities for retrieval

## Component Workflow

### 1. Web Scraping and PDF Collection (`webscrape.py`)

The system begins by collecting PDFs from a web source:

- `get_pdf_links_for_year(year)`: Scrapes a website for PDF links from a specific year
- `download_pdf(url, output_dir)`: Downloads PDFs with retry logic and error handling
- `compress_pdf(input_path, output_dir)`: Compresses PDFs to reduce storage requirements
- `process_year(year, download_dir)`: Orchestrates the download and compression process for all PDFs from a specific year

This component handles the initial data collection phase, which collects the corpus of the documents that will later be used for RAG. This can be adjusted to serve any set of collected documents, though the logic would have to be tweaked depending on the storage format. 

### 2. PDF to Text Conversion (`pdf_to_text.py`)

Once PDFs are collected, we extract text using OCR:

- `pdf_to_text(pdf_path, output_path)`: Converts PDF pages to images and applies OCR to extract text
- The extracted text is saved to text files that maintain the original document structure

This step transforms the visual PDF content into text files that can be processed further. This may also be applicable if the desired collection of sources is in PDF format.

### 3. Text Chunking

The extracted text is divided into manageable chunks using one of two approaches:

#### 3.1 Fixed-Size Chunking (`text_chunker.py`)

- `chunk_text(text, chunk_size, overlap)`: Splits text into overlapping chunks of specified size
- `create_metadata(file_path)`: Extracts metadata from filenames (e.g., dates)
- `process_file(file_path, output_dir)`: Processes a single text file into chunks with metadata
- `process_directory(input_dir, output_dir)`: Processes all text files in a directory

This approach divides text into fixed-size chunks with overlap, which ensures comprehensive coverage but may break semantic units.

#### 3.2 Semantic Chunking (`semantic_chunker.py`)

- `semantic_chunk_text(text, max_chunk_size)`: Splits text based on natural paragraph and sentence boundaries
- `create_metadata(file_path)`: Extracts metadata from filenames (e.g., dates)
- `process_file(file_path, output_dir)`: Processes a single text file into semantic chunks with metadata
- `process_directory(input_dir, output_dir)`: Processes all text files in a directory

Semantic chunking preserves the natural structure of the document by respecting paragraph and sentence boundaries. It attempts to keep related content together while still adhering to maximum chunk size constraints. This approach often results in more coherent chunks that maintain context better than fixed-size chunking.

Chunking is a crucial step for effective retrieval, as it allows the system to return relevant portions of documents rather than entire documents. The choice between fixed-size and semantic chunking depends on the specific requirements of the application.

### 4. Embedding Generation (`embed_chunks.py`)

The chunks are then converted into vector embeddings:

- `load_chunks(file_path)`: Loads chunked text from JSON files
- `generate_embeddings(chunks, model_name)`: Creates vector embeddings for each chunk
- `save_embeddings(embedded_chunks, output_path)`: Saves the embeddings for future use
- `vector_search(query, embedded_chunks, top_k)`: Performs semantic search on the embeddings

This component enables semantic search by converting text into vector representations that capture meaning. Then, given a query, the system searches the embeddings to find the most relevant chunks.

### 5. RAG System Integration (`llm_interface.py` and `archivebot.py`)

The final components integrate the vector search with a language model:

- `LocalLLM`: A class that initializes and manages the language model
- `load_embedded_chunks(embeddings_path)`: Loads the pre-computed embeddings
- `rag_response(query, embedded_chunks, llm, top_k)`: Performs retrieval and generates a response
- Interactive interface for users to ask questions about the archived materials

The system uses a retrieval-augmented generation approach where:
1. User queries are processed to find the most relevant chunks using vector search
2. Retrieved chunks are formatted into a prompt with the original query
3. The language model generates a response based on the retrieved context

This approach allows the system to provide accurate, contextually relevant responses based on the archived materials.

