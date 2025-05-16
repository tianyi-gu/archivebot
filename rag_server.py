#generated with the help of Claude Sonnet 3.7, not yet looked through

import os
import json
import time
import threading
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import subprocess
import pickle
from typing import Dict, Any, List, Optional

# Global state to track pipeline progress
pipeline_state = {
    "scraping": {
        "in_progress": False,
        "completed_urls": [],
        "failed_urls": [],
        "total_urls": 0,
        "current_year": None
    },
    "ocr": {
        "in_progress": False,
        "completed_files": [],
        "failed_files": [],
        "total_files": 0,
        "current_file": None
    },
    "chunking": {
        "in_progress": False,
        "completed_files": [],
        "failed_files": [],
        "total_files": 0,
        "current_file": None
    },
    "embedding": {
        "in_progress": False,
        "completed_chunks": 0,
        "total_chunks": 0
    },
    "model": {
        "loaded": False,
        "name": None
    }
}

# Global variables for the RAG components
embedded_chunks = None
llm = None

# Pipeline execution functions
def run_scraping(years):
    """Run the web scraping process for the specified years"""
    pipeline_state["scraping"]["in_progress"] = True
    pipeline_state["scraping"]["completed_urls"] = []
    pipeline_state["scraping"]["failed_urls"] = []
    pipeline_state["scraping"]["total_urls"] = 0 
    
    try:
        for year in years:
            pipeline_state["scraping"]["current_year"] = year
            print(f"Scraping archives for year {year}...")
            
            # Call the webscrape.py script for each year
            cmd = ["python", "webscrape.py", year]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor the process output to update state
            for line in process.stdout:
                print(line.strip())
                if "Successfully downloaded" in line:
                    url = line.split("from ")[-1].strip()
                    pipeline_state["scraping"]["completed_urls"].append(url)
                elif "Download failed" in line:
                    url = line.split("for ")[-1].strip()
                    pipeline_state["scraping"]["failed_urls"].append(url)
                elif "Found" in line and "PDF links" in line:
                    try:
                        count = int(line.split("Found ")[1].split(" PDF")[0])
                        pipeline_state["scraping"]["total_urls"] += count
                    except:
                        pass
            
            process.wait()
    
    except Exception as e:
        print(f"Error in scraping process: {e}")
    finally:
        # If we didn't find any URLs but completed the process, set total to match completed
        if pipeline_state["scraping"]["total_urls"] == 0 and len(pipeline_state["scraping"]["completed_urls"]) > 0:
            pipeline_state["scraping"]["total_urls"] = len(pipeline_state["scraping"]["completed_urls"])
        
        pipeline_state["scraping"]["in_progress"] = False
        pipeline_state["scraping"]["current_year"] = None

def run_ocr(input_dir="raw_corpus", output_dir="text_corpus"):
    """Run OCR on all compressed PDFs in the input directory"""
    pipeline_state["ocr"]["in_progress"] = True
    pipeline_state["ocr"]["completed_files"] = []
    pipeline_state["ocr"]["failed_files"] = []
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all compressed PDF files
        pdf_files = [f for f in os.listdir(input_dir) if f.endswith("_compressed.pdf")]
        pipeline_state["ocr"]["total_files"] = len(pdf_files)
        
        # If no files found, set progress to 0/0 explicitly
        if len(pdf_files) == 0:
            pipeline_state["ocr"]["total_files"] = 0
            print("No compressed PDF files found for OCR processing")
            return
        
        for pdf_file in pdf_files:
            pipeline_state["ocr"]["current_file"] = pdf_file
            pdf_path = os.path.join(input_dir, pdf_file)
            output_path = os.path.join(output_dir, pdf_file.replace(".pdf", ".txt"))
            
            # Skip if text file already exists
            if os.path.exists(output_path):
                pipeline_state["ocr"]["completed_files"].append(pdf_file)
                continue
            
            print(f"Running OCR on {pdf_file}...")
            
            # Call the pdf_to_text.py script
            cmd = ["python", "pdf_to_text.py", pdf_path, "-o", output_path]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor the process
            success = False
            for line in process.stdout:
                print(line.strip())
                if "Text successfully saved" in line:
                    success = True
            
            process.wait()
            
            if success:
                pipeline_state["ocr"]["completed_files"].append(pdf_file)
            else:
                pipeline_state["ocr"]["failed_files"].append(pdf_file)
    
    except Exception as e:
        print(f"Error in OCR process: {e}")
    finally:
        pipeline_state["ocr"]["in_progress"] = False
        pipeline_state["ocr"]["current_file"] = None

def run_chunking(input_dir="text_corpus", output_dir="chunked_corpus", semantic=True):
    """Run text chunking on all text files in the input directory"""
    pipeline_state["chunking"]["in_progress"] = True
    pipeline_state["chunking"]["completed_files"] = []
    pipeline_state["chunking"]["failed_files"] = []
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all text files
        text_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
        pipeline_state["chunking"]["total_files"] = len(text_files)
        
        # Choose the chunking script based on the semantic flag
        chunker_script = "semantic_chunker.py" if semantic else "text_chunker.py"
        
        # Process all text files
        for text_file in text_files:
            pipeline_state["chunking"]["current_file"] = text_file
            text_path = os.path.join(input_dir, text_file)
            
            print(f"Chunking {text_file}...")
            
            # Call the chunking script
            cmd = ["python", chunker_script, "--input", text_path, "--output", output_dir]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor the process
            success = False
            for line in process.stdout:
                print(line.strip())
                if "Processed" in line and "chunks" in line:
                    success = True
            
            process.wait()
            
            if success:
                pipeline_state["chunking"]["completed_files"].append(text_file)
            else:
                pipeline_state["chunking"]["failed_files"].append(text_file)
    
    except Exception as e:
        print(f"Error in chunking process: {e}")
    finally:
        pipeline_state["chunking"]["in_progress"] = False
        pipeline_state["chunking"]["current_file"] = None

def run_embedding(input_path="chunked_corpus/all_chunks.json", output_path="chunked_corpus/embedded_chunks.pkl"):
    """Generate embeddings for all chunks"""
    pipeline_state["embedding"]["in_progress"] = True
    pipeline_state["embedding"]["completed_chunks"] = 0
    
    try:
        # Call the embed_chunks.py script
        cmd = ["python", "embed_chunks.py", "--input", input_path, "--output", output_path]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Monitor the process
        for line in process.stdout:
            print(line.strip())
            if "Generating embeddings for" in line:
                try:
                    count = int(line.split("for ")[1].split(" chunks")[0])
                    pipeline_state["embedding"]["total_chunks"] = count
                except:
                    pass
            elif "Embeddings saved to" in line:
                pipeline_state["embedding"]["completed_chunks"] = pipeline_state["embedding"]["total_chunks"]
        
        process.wait()
        
        # Load the embeddings
        global embedded_chunks
        if os.path.exists(output_path):
            with open(output_path, 'rb') as f:
                embedded_chunks = pickle.load(f)
                print(f"Loaded embeddings for {len(embedded_chunks['chunks'])} chunks")
    
    except Exception as e:
        print(f"Error in embedding process: {e}")
    finally:
        pipeline_state["embedding"]["in_progress"] = False

def load_llm(model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
    """Load the language model"""
    try:
        # Import here to avoid loading dependencies unless needed
        from llm_interface import LocalLLM
        
        global llm
        print(f"Loading language model: {model_name}")
        llm = LocalLLM(model_name=model_name)
        
        pipeline_state["model"]["loaded"] = True
        pipeline_state["model"]["name"] = model_name
        print("Language model loaded successfully")
    
    except Exception as e:
        print(f"Error loading language model: {e}")
        pipeline_state["model"]["loaded"] = False

def generate_response(query, top_k=3):
    """Generate a response using the RAG system"""
    if not embedded_chunks:
        return "Error: Embeddings not loaded. Please run the embedding process first."
    
    if not llm:
        return "Error: Language model not loaded. Please load the model first."
    
    try:
        # Import here to avoid loading dependencies unless needed
        from llm_interface import rag_response
        
        print(f"Generating response for query: {query}")
        response = rag_response(query, embedded_chunks, llm, top_k=top_k)
        return response
    
    except Exception as e:
        print(f"Error generating response: {e}")
        return f"Error generating response: {str(e)}"

# HTTP Request Handler
class RAGServerHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def _handle_error(self, error_msg, status_code=400):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": error_msg}).encode())
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Serve static files for the web interface
        if path == "/" or path == "":
            self._serve_file("web/index.html", "text/html")
            return
        elif path.startswith("/web/"):
            file_path = path[1:]  # Remove leading slash
            if os.path.exists(file_path):
                content_type = self._get_content_type(file_path)
                self._serve_file(file_path, content_type)
                return
        
        # API endpoints
        if path == "/api/status":
            self._set_headers()
            self.wfile.write(json.dumps(pipeline_state).encode())
        elif path == "/api/query":
            query_params = parse_qs(parsed_path.query)
            if "q" in query_params:
                query = query_params["q"][0]
                top_k = int(query_params.get("top_k", [3])[0])
                response = generate_response(query, top_k)
                self._set_headers()
                self.wfile.write(json.dumps({"response": response}).encode())
            else:
                self._handle_error("Missing query parameter 'q'")
        else:
            self._handle_error("Endpoint not found", 404)
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
        except json.JSONDecodeError:
            self._handle_error("Invalid JSON")
            return
        
        if self.path == "/api/scrape":
            if "years" in data:
                years = data["years"]
                if not pipeline_state["scraping"]["in_progress"]:
                    threading.Thread(target=run_scraping, args=(years,)).start()
                    self._set_headers()
                    self.wfile.write(json.dumps({"status": "started", "years": years}).encode())
                else:
                    self._handle_error("Scraping already in progress")
            else:
                self._handle_error("Missing 'years' parameter")
        
        elif self.path == "/api/ocr":
            if not pipeline_state["ocr"]["in_progress"]:
                input_dir = data.get("input_dir", "raw_corpus")
                output_dir = data.get("output_dir", "text_corpus")
                threading.Thread(target=run_ocr, args=(input_dir, output_dir)).start()
                self._set_headers()
                self.wfile.write(json.dumps({"status": "started", "input_dir": input_dir, "output_dir": output_dir}).encode())
            else:
                self._handle_error("OCR already in progress")
        
        elif self.path == "/api/chunk":
            if not pipeline_state["chunking"]["in_progress"]:
                input_dir = data.get("input_dir", "text_corpus")
                output_dir = data.get("output_dir", "chunked_corpus")
                semantic = data.get("semantic", True)
                threading.Thread(target=run_chunking, args=(input_dir, output_dir, semantic)).start()
                self._set_headers()
                self.wfile.write(json.dumps({
                    "status": "started", 
                    "input_dir": input_dir, 
                    "output_dir": output_dir,
                    "method": "semantic" if semantic else "fixed-size"
                }).encode())
            else:
                self._handle_error("Chunking already in progress")
        
        elif self.path == "/api/embed":
            if not pipeline_state["embedding"]["in_progress"]:
                input_path = data.get("input_path", "chunked_corpus/all_chunks.json")
                output_path = data.get("output_path", "chunked_corpus/embedded_chunks.pkl")
                threading.Thread(target=run_embedding, args=(input_path, output_path)).start()
                self._set_headers()
                self.wfile.write(json.dumps({
                    "status": "started", 
                    "input_path": input_path, 
                    "output_path": output_path
                }).encode())
            else:
                self._handle_error("Embedding already in progress")
        
        elif self.path == "/api/load_model":
            if not pipeline_state["model"]["loaded"]:
                model_name = data.get("model_name", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
                threading.Thread(target=load_llm, args=(model_name,)).start()
                self._set_headers()
                self.wfile.write(json.dumps({"status": "loading", "model_name": model_name}).encode())
            else:
                self._handle_error("Model already loaded")
        
        elif self.path == "/api/query":
            if "query" in data:
                query = data["query"]
                top_k = data.get("top_k", 3)
                response = generate_response(query, top_k)
                self._set_headers()
                self.wfile.write(json.dumps({"response": response}).encode())
            else:
                self._handle_error("Missing 'query' parameter")
        
        else:
            self._handle_error("Endpoint not found", 404)
    
    def _serve_file(self, file_path, content_type):
        """Serve a static file"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self._handle_error(f"File not found: {file_path}", 404)
    
    def _get_content_type(self, file_path):
        """Get the content type based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.html':
            return 'text/html'
        elif ext == '.css':
            return 'text/css'
        elif ext == '.js':
            return 'application/javascript'
        elif ext in ['.jpg', '.jpeg']:
            return 'image/jpeg'
        elif ext == '.png':
            return 'image/png'
        else:
            return 'application/octet-stream'

def main():
    parser = argparse.ArgumentParser(description='RAG Pipeline Server')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=8000, help='Server port')
    parser.add_argument('--load-embeddings', action='store_true', help='Load embeddings on startup')
    parser.add_argument('--embeddings-path', default='chunked_corpus/embedded_chunks.pkl', help='Path to embeddings file')
    parser.add_argument('--load-model', action='store_true', help='Load language model on startup')
    parser.add_argument('--model-name', default='TinyLlama/TinyLlama-1.1B-Chat-v1.0', help='Language model to load')
    
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs("raw_corpus", exist_ok=True)
    os.makedirs("text_corpus", exist_ok=True)
    os.makedirs("chunked_corpus", exist_ok=True)
    os.makedirs("web", exist_ok=True)
    
    # Create a simple web interface if it doesn't exist
    if not os.path.exists("web/index.html"):
        create_web_interface()
    
    # Load embeddings if requested
    if args.load_embeddings and os.path.exists(args.embeddings_path):
        try:
            global embedded_chunks
            with open(args.embeddings_path, 'rb') as f:
                embedded_chunks = pickle.load(f)
                print(f"Loaded embeddings for {len(embedded_chunks['chunks'])} chunks")
        except Exception as e:
            print(f"Error loading embeddings: {e}")
    
    # Load language model if requested
    if args.load_model:
        threading.Thread(target=load_llm, args=(args.model_name,)).start()
    
    # Start the server
    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, RAGServerHandler)
    print(f"Starting RAG Pipeline server on http://{args.host}:{args.port}")
    httpd.serve_forever()

def create_web_interface():
    """Create a simple web interface for the RAG Pipeline"""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ArchiveBot RAG Pipeline</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .panel {
            flex: 1;
            min-width: 300px;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            background-color: #f9f9f9;
        }
        .panel h2 {
            margin-top: 0;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 15px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        input, select {
            width: 100%;
            padding: 8px;
            margin: 8px 0;
            display: inline-block;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .progress {
            margin-top: 10px;
            padding: 10px;
            background-color: #e9e9e9;
            border-radius: 4px;
        }
        .chat-container {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-top: 20px;
            height: 300px;
            overflow-y: auto;
        }
        .message {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background-color: #e3f2fd;
            text-align: right;
        }
        .bot-message {
            background-color: #f1f1f1;
        }
    </style>
</head>
<body>
    <h1>ArchiveBot RAG Pipeline</h1>
    
    <div class="container">
        <div class="panel">
            <h2>1. Web Scraping</h2>
            <div>
                <label for="years">Years to scrape (comma-separated):</label>
                <input type="text" id="years" placeholder="2023,2022,2021">
                <button id="scrapeBtn">Start Scraping</button>
            </div>
            <div class="progress" id="scrapeProgress">
                <div>Status: <span id="scrapeStatus">Not started</span></div>
                <div>Current year: <span id="scrapeYear">None</span></div>
                <div>Progress: <span id="scrapeCompleted">0</span>/<span id="scrapeTotal">0</span></div>
                <div>Percentage: <span id="scrapePercent">0%</span></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>2. OCR Processing</h2>
            <div>
                <button id="ocrBtn">Start OCR</button>
            </div>
            <div class="progress" id="ocrProgress">
                <div>Status: <span id="ocrStatus">Not started</span></div>
                <div>Current file: <span id="ocrFile">None</span></div>
                <div>Progress: <span id="ocrCompleted">0</span>/<span id="ocrTotal">0</span></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>3. Text Chunking</h2>
            <div>
                <label for="chunkMethod">Chunking method:</label>
                <select id="chunkMethod">
                    <option value="semantic">Semantic Chunking</option>
                    <option value="fixed">Fixed-Size Chunking</option>
                </select>
                <button id="chunkBtn">Start Chunking</button>
            </div>
            <div class="progress" id="chunkProgress">
                <div>Status: <span id="chunkStatus">Not started</span></div>
                <div>Current file: <span id="chunkFile">None</span></div>
                <div>Progress: <span id="chunkCompleted">0</span>/<span id="chunkTotal">0</span></div>
            </div>
        </div>
        
        <div class="panel">
            <h2>4. Embedding Generation</h2>
            <div>
                <button id="embedBtn">Generate Embeddings</button>
            </div>
            <div class="progress" id="embedProgress">
                <div>Status: <span id="embedStatus">Not started</span></div>
                <div>Progress: <span id="embedCompleted">0</span>/<span id="embedTotal">0</span></div>
            </div>
        </div>
    </div>
    
    <div class="panel" style="margin-top: 20px;">
        <h2>5. Load Language Model</h2>
        <div>
            <label for="modelName">Model name:</label>
            <input type="text" id="modelName" value="TinyLlama/TinyLlama-1.1B-Chat-v1.0">
            <button id="loadModelBtn">Load Model</button>
        </div>
        <div class="progress" id="modelProgress">
            <div>Status: <span id="modelStatus">Not loaded</span></div>
            <div>Model: <span id="loadedModel">None</span></div>
        </div>
    </div>
    
    <div class="panel" style="margin-top: 20px;">
        <h2>6. Chat with ArchiveBot</h2>
        <div class="chat-container" id="chatContainer"></div>
        <div style="display: flex; margin-top: 10px;">
            <input type="text" id="queryInput" placeholder="Ask a question..." style="flex: 1;">
            <button id="sendBtn" style="margin-left: 10px;">Send</button>
        </div>
    </div>
    
    <script>
        // Function to update the UI with the current pipeline state
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update scraping status
                    const scraping = data.scraping;
                    document.getElementById('scrapeStatus').textContent = scraping.in_progress ? 'In progress' : 'Idle';
                    document.getElementById('scrapeYear').textContent = scraping.current_year || 'None';
                    document.getElementById('scrapeCompleted').textContent = scraping.completed_urls.length;
                    document.getElementById('scrapeTotal').textContent = scraping.total_urls;
                    
                    // Add progress percentage
                    const scrapePercent = scraping.total_urls > 0 ? 
                        Math.round((scraping.completed_urls.length / scraping.total_urls) * 100) : 0;
                    document.getElementById('scrapePercent').textContent = `${scrapePercent}%`;
                    
                    // Update OCR status
                    const ocr = data.ocr;
                    document.getElementById('ocrStatus').textContent = ocr.in_progress ? 'In progress' : 'Idle';
                    document.getElementById('ocrFile').textContent = ocr.current_file || 'None';
                    document.getElementById('ocrCompleted').textContent = ocr.completed_files.length;
                    document.getElementById('ocrTotal').textContent = ocr.total_files;
                    document.getElementById('ocrBtn').disabled = ocr.in_progress;
                    
                    // Update chunking status
                    const chunking = data.chunking;
                    document.getElementById('chunkStatus').textContent = chunking.in_progress ? 'In progress' : 'Idle';
                    document.getElementById('chunkFile').textContent = chunking.current_file || 'None';
                    document.getElementById('chunkCompleted').textContent = chunking.completed_files.length;
                    document.getElementById('chunkTotal').textContent = chunking.total_files;
                    document.getElementById('chunkBtn').disabled = chunking.in_progress;
                    
                    // Update embedding status
                    const embedding = data.embedding;
                    document.getElementById('embedStatus').textContent = embedding.in_progress ? 'In progress' : 'Idle';
                    document.getElementById('embedCompleted').textContent = embedding.completed_chunks;
                    document.getElementById('embedTotal').textContent = embedding.total_chunks;
                    document.getElementById('embedBtn').disabled = embedding.in_progress;
                    
                    // Update model status
                    const model = data.model;
                    document.getElementById('modelStatus').textContent = model.loaded ? 'Loaded' : 'Not loaded';
                    document.getElementById('loadedModel').textContent = model.name || 'None';
                    document.getElementById('loadModelBtn').disabled = model.loaded;
                })
                .catch(error => console.error('Error fetching status:', error));
        }
        
        // Initialize and set up event listeners
        document.addEventListener('DOMContentLoaded', function() {
            // Start periodic status updates
            updateStatus();
            setInterval(updateStatus, 2000);
            
            // Scraping button
            document.getElementById('scrapeBtn').addEventListener('click', function() {
                const years = document.getElementById('years').value.split(',').map(y => y.trim());
                if (years.length === 0 || years[0] === '') {
                    alert('Please enter at least one year');
                    return;
                }
                
                fetch('/api/scrape', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ years: years })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => console.error('Error starting scraping:', error));
            });
            
            // OCR button
            document.getElementById('ocrBtn').addEventListener('click', function() {
                fetch('/api/ocr', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => console.error('Error starting OCR:', error));
            });
            
            // Chunking button
            document.getElementById('chunkBtn').addEventListener('click', function() {
                const semantic = document.getElementById('chunkMethod').value === 'semantic';
                
                fetch('/api/chunk', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ semantic: semantic })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => console.error('Error starting chunking:', error));
            });
            
            // Embedding button
            document.getElementById('embedBtn').addEventListener('click', function() {
                fetch('/api/embed', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => console.error('Error starting embedding generation:', error));
            });
            
            // Load model button
            document.getElementById('loadModelBtn').addEventListener('click', function() {
                const modelName = document.getElementById('modelName').value;
                
                fetch('/api/load_model', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ model_name: modelName })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => console.error('Error loading model:', error));
            });
            
            // Chat functionality
            document.getElementById('sendBtn').addEventListener('click', function() {
                sendQuery();
            });
            
            document.getElementById('queryInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendQuery();
                }
            });
            
            function sendQuery() {
                const query = document.getElementById('queryInput').value.trim();
                if (!query) return;
                
                // Add user message to chat
                addMessage(query, 'user');
                document.getElementById('queryInput').value = '';
                
                // Show loading indicator
                addMessage('Thinking...', 'bot', true);
                
                fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query: query })
                })
                .then(response => response.json())
                .then(data => {
                    // Remove loading indicator
                    const loadingElement = document.querySelector('.loading-message');
                    if (loadingElement) {
                        loadingElement.remove();
                    }
                    
                    if (data.error) {
                        addMessage('Error: ' + data.error, 'bot');
                    } else {
                        addMessage(data.response, 'bot');
                    }
                })
                .catch(error => {
                    console.error('Error sending query:', error);
                    // Remove loading indicator
                    const loadingElement = document.querySelector('.loading-message');
                    if (loadingElement) {
                        loadingElement.remove();
                    }
                    addMessage('Error communicating with server', 'bot');
                });
            }
            
            function addMessage(text, sender, isLoading = false) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}-message`;
                if (isLoading) {
                    messageDiv.className += ' loading-message';
                }
                messageDiv.textContent = text;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        });
    </script>
</body>
</html>
"""
    
    # Write the HTML to a file
    with open("web/index.html", "w") as f:
        f.write(html)
    
    print("Created web interface at web/index.html")

if __name__ == "__main__":
    main()