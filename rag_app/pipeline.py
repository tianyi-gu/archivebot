import os
import subprocess
import pickle
import json
from typing import Dict, Any, List, Optional
from django.conf import settings
import sys

# Import your existing pipeline functions
# Modify them to update the database state

def run_scraping(years, state):
    """Run the web scraping process for the specified years"""
    try:
        # First, estimate total URLs by doing a quick scan
        print("Estimating total URLs to scrape...")
        estimated_total = 0
        
        for year in years:
            try:
                # For now, we'll estimate based on typical archive sizes
                estimated_total += 30  
            except:
                pass
        
        state.scraping_total_urls = estimated_total
        state.save()
        
        # Now do the actual scraping
        for year in years:
            state.scraping_current_year = year
            state.save()
            print(f"Scraping archives for year {year}...")
            
            # Call the webscrape.py script for each year
            script_path = os.path.join(settings.BASE_DIR, "scripts", "webscrape.py")
            cmd = ["python", script_path, year]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor the process output to update state
            for line in process.stdout:
                print(line.strip())
                if "Successfully downloaded" in line:
                    url = line.split("from ")[-1].strip()
                    current_completed = state.scraping_completed_urls.copy()
                    current_completed.append(url)
                    state.scraping_completed_urls = current_completed
                    state.save()
                elif "Download failed" in line:
                    url = line.split("for ")[-1].strip()
                    current_failed = state.scraping_failed_urls.copy()
                    current_failed.append(url)
                    state.scraping_failed_urls = current_failed
                    state.save()
                elif "Found" in line and "PDF links" in line:
                    try:
                        count = int(line.split("Found ")[1].split(" PDF")[0])
                        # Update total with actual count
                        state.scraping_total_urls = max(state.scraping_total_urls, 
                                                      len(state.scraping_completed_urls) + 
                                                      len(state.scraping_failed_urls) + count)
                        state.save()
                    except:
                        pass
            
            process.wait()
    
    except Exception as e:
        print(f"Error in scraping process: {e}")
    finally:
        # Ensure we have accurate totals
        total_processed = len(state.scraping_completed_urls) + len(state.scraping_failed_urls)
        if state.scraping_total_urls < total_processed:
            state.scraping_total_urls = total_processed
            state.save()

def run_ocr(state, input_dir=None, output_dir=None):
    """Run OCR on all compressed PDFs in the input directory"""
    if input_dir is None:
        input_dir = str(settings.RAW_CORPUS_DIR)
    if output_dir is None:
        output_dir = str(settings.TEXT_CORPUS_DIR)
        
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
            script_path = os.path.join(settings.BASE_DIR, "scripts", "pdf_to_text.py")
            cmd = ["python", script_path, pdf_path, "-o", output_path]
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

def run_chunking(semantic, state, input_dir=None, output_dir=None):
    """Run text chunking on all text files in the input directory"""
    if input_dir is None:
        input_dir = str(settings.TEXT_CORPUS_DIR)
    if output_dir is None:
        output_dir = str(settings.CHUNKED_CORPUS_DIR)
        
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all text files
        text_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
        state.chunking_total_files = len(text_files)
        state.save()
        
        # Choose the chunking script based on the semantic flag
        chunker_script = "semantic_chunker.py" if semantic else "text_chunker.py"
        script_path = os.path.join(settings.BASE_DIR, "scripts", chunker_script)
        
        # Process all text files
        for text_file in text_files:
            state.chunking_current_file = text_file
            state.save()
            
            text_path = os.path.join(input_dir, text_file)
            
            print(f"Chunking {text_file}...")
            
            # Call the chunking script
            cmd = ["python", script_path, "--input", text_path, "--output", output_dir]
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

def run_embedding(state, input_path=None, output_path=None):
    """Generate embeddings for all chunks"""
    if input_path is None:
        input_path = os.path.join(str(settings.CHUNKED_CORPUS_DIR), "all_chunks.json")
    if output_path is None:
        output_path = os.path.join(str(settings.CHUNKED_CORPUS_DIR), "embedded_chunks.pkl")
        
    try:
        # Call the embed_chunks.py script
        script_path = os.path.join(settings.BASE_DIR, "scripts", "embed_chunks.py")
        cmd = ["python", script_path, "--input", input_path, "--output", output_path]
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
        from .llm_interface import LocalLLM
        
        print(f"Loading model: {model_name}")
        llm = LocalLLM(model_name=model_name)
        return llm
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def generate_response(query, embedded_chunks, llm, top_k=3):
    """Generate a response to a query using RAG"""
    try:
        from .llm_interface import rag_response
        
        response = rag_response(query, embedded_chunks, llm, top_k)
        return response
    except Exception as e:
        print(f"Error generating response: {e}")
        raise 