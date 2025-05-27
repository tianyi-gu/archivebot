# Archivebot

Created by [Tianyi Gu](https://github.com/tianyi-gu) for CSC600: Computer Science Research and Development at Phillips Academy.

## Final Artifact Description

Archivebot is a RAG (Retrieval-Augmented Generation) based system that allows users to work with corpus of archived documents in an easy and accessible way. This project is the culmination of my research and development work throughout the term, throughout which I aimed to build a practical application which I could both learn from building and could serve as a helpful tool for the school community.

**It is accessible here: [https://github.com/tianyi-gu/archivebot](https://github.com/tianyi-gu/archivebot).**

The system enables users to choose selected document collections to process and index for semantic search, and provides an intelligent chat interface where users can ask questions about their archived content. The bot retrieves relevant document passages and generates contextual responses, making large document collections more accessible and queryable through natural language.

## How to Access and Evaluate This Project

This submission contains a fully functional web application built with Django. To run and evaluate the project:

1. **Setup**: Navigate to the `archivebot_project` directory and follow the installation instructions in the main README.md file
2. **Running**: Use the provided Django management commands to start the development server
3. **Testing**: Upload sample documents through the web interface and interact with the chat system to see the RAG capabilities in action

## Project Structure

- **Backend**: Django-based REST API handling document processing, embedding generation, and chat functionality
- **Frontend**: Simple interface for document upload and chat interaction
- **AI/ML Components**: Integration with embedding models and language models for RAG implementation
- **Database**: Efficient storage and retrieval of documents and embeddings

