import json
import threading
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PipelineState, ChatMessage

# Import existing pipeline functions
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

def status(request):
    """Get the current status of all pipeline components"""
    state = PipelineState.get_instance()
    
    return JsonResponse({
        "scraping": {
            "in_progress": state.scraping_in_progress,
            "current_year": state.scraping_current_year,
            "completed_urls": state.scraping_completed_urls,
            "failed_urls": state.scraping_failed_urls,
            "total_urls": state.scraping_total_urls,
        },
        "ocr": {
            "in_progress": state.ocr_in_progress,
            "current_file": state.ocr_current_file,
            "completed_files": state.ocr_completed_files,
            "failed_files": state.ocr_failed_files,
            "total_files": state.ocr_total_files,
        },
        "chunking": {
            "in_progress": state.chunking_in_progress,
            "current_file": state.chunking_current_file,
            "completed_files": state.chunking_completed_files,
            "total_files": state.chunking_total_files,
        },
        "embedding": {
            "in_progress": state.embedding_in_progress,
            "completed_chunks": state.embedding_completed_chunks,
            "total_chunks": state.embedding_total_chunks,
        },
        "model": {
            "loaded": state.model_loaded,
            "name": state.model_name,
        }
    })

@csrf_exempt
def scrape(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            years = data.get('years', [])
            
            if not years:
                return JsonResponse({"error": "No years provided"}, status=400)
            
            state = PipelineState.get_instance()
            if state.scraping_in_progress:
                return JsonResponse({"error": "Scraping already in progress"}, status=400)
            
            def scrape_thread():
                try:
                    print(f"Starting scraping for years: {years}")
                    state.scraping_in_progress = True
                    state.scraping_completed_urls = []
                    state.scraping_failed_urls = []
                    state.scraping_total_urls = 0
                    state.save()
                    print("Scraping state initialized")
                    
                    run_scraping(years, state)
                    print("Scraping completed successfully")
                except Exception as e:
                    print(f"Error in scraping thread: {e}")
                finally:
                    state.scraping_in_progress = False
                    state.save()
                    print("Scraping thread finished")
            
            threading.Thread(target=scrape_thread, daemon=True).start()
            print("Scraping thread started")
            
            return JsonResponse({"message": "Scraping started"})
        except Exception as e:
            print(f"Error in scrape view: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def ocr(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            years_filter = data.get('years', None)  # Optional years filter
            
            state = PipelineState.get_instance()
            if state.ocr_in_progress:
                return JsonResponse({"error": "OCR already in progress"}, status=400)
            
            def ocr_thread():
                try:
                    print(f"Starting OCR processing with years filter: {years_filter}")
                    state.ocr_in_progress = True
                    state.ocr_completed_files = []
                    state.ocr_failed_files = []
                    state.ocr_total_files = 0
                    state.save()
                    print("OCR state initialized")
                    
                    run_ocr(state, years_filter=years_filter)
                    print("OCR completed successfully")
                except Exception as e:
                    print(f"Error in OCR thread: {e}")
                finally:
                    state.ocr_in_progress = False
                    state.save()
                    print("OCR thread finished")
            
            threading.Thread(target=ocr_thread, daemon=True).start()
            print("OCR thread started")
            
            return JsonResponse({"message": "OCR started"})
        except Exception as e:
            print(f"Error in OCR view: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def chunk(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            semantic = data.get('semantic', True)
            
            state = PipelineState.get_instance()
            if state.chunking_in_progress:
                return JsonResponse({"error": "Chunking already in progress"}, status=400)
            
            def chunk_thread():
                try:
                    state.chunking_in_progress = True
                    state.save()
                    run_chunking(semantic, state)
                finally:
                    state.chunking_in_progress = False
                    state.save()
            
            threading.Thread(target=chunk_thread, daemon=True).start()
            
            return JsonResponse({"message": "Chunking started"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def embed(request):
    if request.method == 'POST':
        try:
            state = PipelineState.get_instance()
            if state.embedding_in_progress:
                return JsonResponse({"error": "Embedding already in progress"}, status=400)
            
            def embed_thread():
                global embedded_chunks
                try:
                    state.embedding_in_progress = True
                    state.save()
                    # Store the result in the global variable
                    embedded_chunks = run_embedding(state)
                finally:
                    state.embedding_in_progress = False
                    state.save()
            
            threading.Thread(target=embed_thread, daemon=True).start()
            
            return JsonResponse({"message": "Embedding generation started"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def load_model(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            model_name = data.get('model_name', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
            
            state = PipelineState.get_instance()
            if state.model_loaded:
                return JsonResponse({"error": "Model already loaded"}, status=400)
            
            print(f"Loading model: {model_name}") 
            
            global llm
            llm = load_llm(model_name)
            
            print(f"Model loaded successfully: {llm is not None}") 
            
            if llm:
                state.model_loaded = True
                state.model_name = model_name
                state.save()
                print(f"Model {model_name} loaded and state updated")  
                return JsonResponse({"message": f"Model {model_name} loaded successfully"})
            else:
                print("Failed to load model")  
                return JsonResponse({"error": "Failed to load model"}, status=500)
                
        except Exception as e:
            print(f"Exception in load_model: {e}")  
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def query(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query_text = data.get('query', '')
            
            print(f"Received query: '{query_text}'")  # Debug log
            
            if not query_text:
                print("Error: No query provided")  # Debug log
                return JsonResponse({"error": "No query provided"}, status=400)
            
            global llm, embedded_chunks
            
            print(f"LLM loaded: {llm is not None}")  # Debug log
            print(f"Embedded chunks loaded: {embedded_chunks is not None}")  # Debug log
            
            if not llm:
                print("Error: Model not loaded")  # Debug log
                return JsonResponse({"error": "Model not loaded"}, status=400)
            
            # Load embeddings if not already loaded
            if not embedded_chunks:
                print("Loading embeddings...")  # Debug log
                from django.conf import settings
                import os
                embeddings_path = os.path.join(settings.CHUNKED_CORPUS_DIR, "embedded_chunks.pkl")
                print(f"Looking for embeddings at: {embeddings_path}")  # Debug log
                if os.path.exists(embeddings_path):
                    from .llm_interface import load_embedded_chunks
                    embedded_chunks = load_embedded_chunks(embeddings_path)
                    print(f"Embeddings loaded: {embedded_chunks is not None}")  # Debug log
                else:
                    print("Error: Embeddings file not found")  # Debug log
                    return JsonResponse({"error": "Embeddings not found. Please run embedding generation first."}, status=400)
            
            if not embedded_chunks:
                print("Error: Failed to load embeddings")  # Debug log
                return JsonResponse({"error": "Failed to load embeddings"}, status=400)
            
            print("Generating response...")  # Debug log
            response = generate_response(query_text, embedded_chunks, llm)
            print(f"Response generated: {response[:100]}...")  # Debug log (first 100 chars)
            
            # Save to chat history
            ChatMessage.objects.create(
                message=query_text,
                response=response,
                is_user=True
            )
            
            return JsonResponse({"response": response})
            
        except Exception as e:
            print(f"Exception in query view: {e}")  # Debug log
            import traceback
            traceback.print_exc()  # Print full traceback
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

def chat_history(request):
    """Get chat history"""
    messages = ChatMessage.objects.all().order_by('timestamp')
    history = []
    
    for msg in messages:
        history.append({
            "message": msg.message,
            "response": msg.response,
            "timestamp": msg.timestamp.isoformat(),
            "is_user": msg.is_user
        })
    
    return JsonResponse({"history": history})

@csrf_exempt
def reset_state(request):
    if request.method == 'POST':
        try:
            global llm, embedded_chunks
            llm = None
            embedded_chunks = None
            
            state = PipelineState.get_instance()
            state.scraping_in_progress = False
            state.scraping_completed_urls = []
            state.scraping_failed_urls = []
            state.scraping_total_urls = 0
            state.scraping_current_year = None
            state.ocr_in_progress = False
            state.chunking_in_progress = False
            state.embedding_in_progress = False
            state.model_loaded = False
            state.model_name = None
            state.save()
            
            return JsonResponse({"message": "State reset successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405) 