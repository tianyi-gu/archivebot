import json
import threading
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PipelineState, ChatMessage

# Import your existing pipeline functions
from .pipeline import (
    run_scraping, run_ocr, run_chunking, 
    run_embedding, load_llm, generate_response
)

# Global variables for the RAG components
embedded_chunks = None
llm = None

def index(request):
    """Render the main page"""
    return render(request, 'rag_app/index.html')

def get_status(request):
    """Return the current pipeline state"""
    state = PipelineState.get_instance()
    
    # Convert to the format expected by the frontend
    status = {
        "scraping": {
            "in_progress": state.scraping_in_progress,
            "completed_urls": state.scraping_completed_urls,
            "failed_urls": state.scraping_failed_urls,
            "total_urls": state.scraping_total_urls,
            "current_year": state.scraping_current_year
        },
        "ocr": {
            "in_progress": state.ocr_in_progress,
            "completed_files": state.ocr_completed_files,
            "failed_files": state.ocr_failed_files,
            "total_files": state.ocr_total_files,
            "current_file": state.ocr_current_file
        },
        "chunking": {
            "in_progress": state.chunking_in_progress,
            "completed_files": state.chunking_completed_files,
            "failed_files": state.chunking_failed_files,
            "total_files": state.chunking_total_files,
            "current_file": state.chunking_current_file
        },
        "embedding": {
            "in_progress": state.embedding_in_progress,
            "completed_chunks": state.embedding_completed_chunks,
            "total_chunks": state.embedding_total_chunks
        },
        "model": {
            "loaded": state.model_loaded,
            "name": state.model_name
        }
    }
    
    return JsonResponse(status)

@csrf_exempt
def start_scraping(request):
    """Start the web scraping process"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            years = data.get('years', [])
            
            if not years:
                return JsonResponse({"error": "No years provided"}, status=400)
            
            state = PipelineState.get_instance()
            if state.scraping_in_progress:
                return JsonResponse({"error": "Scraping already in progress"}, status=400)
            
            # Start scraping in a separate thread
            threading.Thread(target=run_scraping_with_state_update, args=(years,)).start()
            
            return JsonResponse({"status": "Scraping started"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

def run_scraping_with_state_update(years):
    """Run scraping and update the state in the database"""
    state = PipelineState.get_instance()
    state.scraping_in_progress = True
    state.scraping_completed_urls = []
    state.scraping_failed_urls = []
    state.scraping_total_urls = 0
    state.save()
    
    try:
        # Call your existing scraping function, modified to update the database
        run_scraping(years, state)
    finally:
        state.scraping_in_progress = False
        state.scraping_current_year = None
        state.save()

# Similar functions for OCR, chunking, embedding, and model loading
@csrf_exempt
def start_ocr(request):
    if request.method == 'POST':
        state = PipelineState.get_instance()
        if state.ocr_in_progress:
            return JsonResponse({"error": "OCR already in progress"}, status=400)
        
        threading.Thread(target=run_ocr_with_state_update).start()
        return JsonResponse({"status": "OCR started"})
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

def run_ocr_with_state_update():
    state = PipelineState.get_instance()
    state.ocr_in_progress = True
    state.ocr_completed_files = []
    state.ocr_failed_files = []
    state.ocr_total_files = 0
    state.save()
    
    try:
        run_ocr(state)
    finally:
        state.ocr_in_progress = False
        state.ocr_current_file = None
        state.save()

@csrf_exempt
def start_chunking(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            semantic = data.get('semantic', True)
            
            state = PipelineState.get_instance()
            if state.chunking_in_progress:
                return JsonResponse({"error": "Chunking already in progress"}, status=400)
            
            threading.Thread(target=run_chunking_with_state_update, args=(semantic,)).start()
            return JsonResponse({"status": "Chunking started"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

def run_chunking_with_state_update(semantic):
    state = PipelineState.get_instance()
    state.chunking_in_progress = True
    state.chunking_completed_files = []
    state.chunking_failed_files = []
    state.chunking_total_files = 0
    state.save()
    
    try:
        run_chunking(semantic, state)
    finally:
        state.chunking_in_progress = False
        state.chunking_current_file = None
        state.save()

@csrf_exempt
def start_embedding(request):
    if request.method == 'POST':
        state = PipelineState.get_instance()
        if state.embedding_in_progress:
            return JsonResponse({"error": "Embedding generation already in progress"}, status=400)
        
        threading.Thread(target=run_embedding_with_state_update).start()
        return JsonResponse({"status": "Embedding generation started"})
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

def run_embedding_with_state_update():
    global embedded_chunks
    
    state = PipelineState.get_instance()
    state.embedding_in_progress = True
    state.embedding_completed_chunks = 0
    state.embedding_total_chunks = 0
    state.save()
    
    try:
        embedded_chunks = run_embedding(state)
    finally:
        state.embedding_in_progress = False
        state.save()

@csrf_exempt
def load_model_view(request):
    if request.method == 'POST':
        try:
            global llm
            
            data = json.loads(request.body)
            model_name = data.get('model_name', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
            
            state = PipelineState.get_instance()
            if state.model_loaded:
                return JsonResponse({"error": "Model already loaded"}, status=400)
            
            state.model_loaded = False
            state.model_name = None
            state.save()
            
            llm = load_llm(model_name)
            
            state.model_loaded = True
            state.model_name = model_name
            state.save()
            
            return JsonResponse({"status": "Model loaded successfully"})
        except Exception as e:
            state = PipelineState.get_instance()
            state.model_loaded = False
            state.model_name = None
            state.save()
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def query(request):
    if request.method == 'POST':
        try:
            global embedded_chunks, llm
            
            data = json.loads(request.body)
            query_text = data.get('query', '')
            
            if not query_text:
                return JsonResponse({"error": "No query provided"}, status=400)
            
            state = PipelineState.get_instance()
            if not state.model_loaded or llm is None:
                return JsonResponse({"error": "Model not loaded"}, status=400)
            
            if embedded_chunks is None:
                return JsonResponse({"error": "Embeddings not generated"}, status=400)
            
            # Save user message
            ChatMessage.objects.create(sender='user', content=query_text)
            
            # Generate response
            response = generate_response(query_text, embedded_chunks, llm)
            
            # Save bot message
            ChatMessage.objects.create(sender='bot', content=response)
            
            return JsonResponse({"response": response})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

def get_chat_history(request):
    """Return the chat history"""
    messages = ChatMessage.objects.all()
    history = [{"sender": msg.sender, "content": msg.content} for msg in messages]
    return JsonResponse({"history": history}) 