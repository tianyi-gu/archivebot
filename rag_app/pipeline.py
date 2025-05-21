import os
import subprocess
import pickle
from typing import Dict, Any, List, Optional

# Import your existing pipeline functions
# Modify them to update the database state

def run_scraping(years, state):
    """Run the web scraping process for the specified years"""
    try:
        for year in years:
            state.scraping_current_year = year
            state.save()
            print(f"Scraping archives for year {year}...")
            
            # Call the webscrape.py script for each year
            cmd = ["python", "webscrape.py", year]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor the process output to update state
            for line in process.stdout:
                print(line.strip())
                if "Successfully downloaded" in line:
                    url = line.split("from ")[-1].strip()
                    state.scraping_completed_urls.append(url)
                    state.save()
                elif "Download failed" in line:
                    url = line.split("for ")[-1].strip()
                    state.scraping_failed_urls.append(url)
                    state.save()
                elif "Found" in line and "PDF links" in line:
                    try:
                        count = int(line.split("Found ")[1].split(" PDF")[0])
                        state.scraping_total_urls += count
                        state.save()
                    except:
                        pass
            
            process.wait()
    
    except Exception as e:
        print(f"Error in scraping process: {e}")
    finally:
        # If we didn't find any URLs but completed the process, set total to match completed
        if state.scraping_total_urls == 0 and len(state.scraping_completed_urls) > 0:
            state.scraping_total_urls = len(state.scraping_completed_urls)
            state.save()

def run_ocr(state, input_dir="raw_corpus", output_dir="text_corpus"):
    """Run OCR on all compressed PDFs in the input directory"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all compressed PDF files
        pdf_files = [f for f in os.listdir(input_dir) if f.endswith("_compressed.pdf")]
        state.ocr_total_files = len(pdf_files)
        state.save()
        
        # If no files found, set progress to 0/0 explicitly
        if len(pdf_files) == 0:
            print("No compressed PDF files found for OCR processing")
            return
        
        for pdf_file in pdf_files:
            state.ocr_current_file = pdf_file
            state.save()
            
            pdf_path = os.path.join(input_dir, pdf_file)
            output_path = os.path.join(output_dir, pdf_file.replace(".pdf", ".txt"))
            
            # Skip if text file already exists
            if os.path.exists(output_path):
                state.ocr_completed_files.append(pdf_file)
                state.save()
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
                state.ocr_completed_files.append(pdf_file)
            else:
                state.ocr_failed_files.append(pdf_file)
            state.save()
    
    except Exception as e:
        print(f"Error in OCR process: {e}")

# Similarly adapt run_chunking, run_embedding, load_llm, and generate_response functions
# to work with the Django state model

def run_chunking(semantic, state, input_dir="text_corpus", output_dir="chunked_corpus"):
    """Run text chunking on all text files in the input directory"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all text files
        text_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
        state.chunking_total_files = len(text_files)
        state.save()
        
        # Choose the chunking script based on the semantic flag
        chunker_script = "semantic_chunker.py" if semantic else "text_chunker.py"
        
        # Process all text files
        for text_file in text_files:
            state.chunking_current_file = text_file
            state.save()
            
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
                state.chunking_completed_files.append(text_file)
            else:
                state.chunking_failed_files.append(text_file)
            state.save()
    
    except Exception as e:
        print(f"Error in chunking process: {e}")

def run_embedding(state, input_path="chunked_corpus/all_chunks.json", output_path="chunked_corpus/embedded_chunks.pkl"):
    """Generate embeddings for all chunks"""
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
                    state.embedding_total_chunks = count
                    state.save()
                except:
                    pass
            elif "Embeddings saved to" in line:
                state.embedding_completed_chunks = state.embedding_total_chunks
                state.save()
        
        process.wait()
        
        # Load the embeddings
        if os.path.exists(output_path):
            with open(output_path, 'rb') as f:
                embedded_chunks = pickle.load(f)
                print(f"Loaded embeddings for {len(embedded_chunks['chunks'])} chunks")
                return embedded_chunks
        return None
    
    except Exception as e:
        print(f"Error in embedding process: {e}")
        return None

def load_llm(model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
    """Load the language model"""
    try:
        # Import here to avoid loading dependencies unless needed
        from llm_interface import LocalLLM
        
        print(f"Loading language model: {model_name}")
        llm = LocalLLM(model_name=model_name)
        
        print("Language model loaded successfully")
        return llm
    
    except Exception as e:
        print(f"Error loading language model: {e}")
        raise

def generate_response(query, embedded_chunks, llm, top_k=3):
    """Generate a response to a query using RAG"""
    try:
        # Import here to avoid loading dependencies unless needed
        from llm_interface import rag_response
        
        response = rag_response(query, embedded_chunks, llm, top_k)
        return response
    
    except Exception as e:
        print(f"Error generating response: {e}")
        raise 