import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import pickle
from typing import List, Dict, Any

class LocalLLM:
    def __init__(self, model_name="microsoft/DialoGPT-medium", device=None): 
        print(f"Loading model: {model_name}")
        
        # auto-detect device if not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        
        self.device = device
        print(f"Using device: {device}")
        
        # load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Add padding token if it doesn't exist
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Fix: Use torch_dtype and proper device handling
        if device == "cuda":
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                device_map="auto",
                load_in_8bit=True,
                torch_dtype=torch.float16
            )
        else:
            # For MPS and CPU, use float32 for better stability
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            self.model = self.model.to(device)
        
        # Don't use pipeline for better control
        print("Model loaded successfully")
    
    def generate_response(self, prompt, max_new_tokens=50, temperature=0.2):
        try:
            # Better prompt length handling
            if len(prompt) > 1200:
                prompt = prompt[-1200:]
            
            # Tokenize with better parameters
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=400,
                padding=False
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Faster generation parameters
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    top_k=30,  # Reduced from 40
                    repetition_penalty=1.1,  # Reduced from 1.15
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    use_cache=True
                )
            
            # Decode only the new tokens
            input_length = inputs['input_ids'].shape[1]
            generated_tokens = outputs[0][input_length:]
            generated_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            # Simpler response cleaning
            response = generated_text.strip()
            
            # Remove common artifacts
            response = response.replace("</s>", "").replace("<s>", "")
            
            # Stop at first natural break point
            stop_phrases = ["\n\n", "Question:", "QUESTION:"]
            for phrase in stop_phrases:
                if phrase in response:
                    response = response.split(phrase)[0]
                    break
            
            # Take first complete sentence if too long
            if len(response) > 150:
                sentences = response.split('.')
                if len(sentences) > 1:
                    response = sentences[0].strip() + "."
            
            return response if response else "I couldn't find relevant information to answer your question."
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Error generating response."

    def validate_response(self, response, query):
        """Validate if the response makes sense"""
        if not response or len(response.strip()) < 10:
            return False
        
        # Check for repetitive text
        words = response.split()
        if len(set(words)) < len(words) * 0.5:  # Too much repetition
            return False
        
        # Check if response is just repeating the query
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        if len(query_words.intersection(response_words)) > len(query_words) * 0.8:
            return False
        
        return True

def load_embedded_chunks(embeddings_path):
    try:
        with open(embeddings_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading embeddings from {embeddings_path}: {e}")
        return None

def rag_response(query, embedded_chunks, llm, top_k=2, max_context_length=600):
    # Add scripts directory to Python path
    import sys
    import os
    from django.conf import settings
    
    scripts_path = os.path.join(settings.BASE_DIR, "scripts")
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    
    # Import after adding to sys.path
    try:
        from embed_chunks import vector_search # type: ignore
    except ImportError as e:
        print(f"Error importing embed_chunks: {e}")
        print(f"Scripts path: {scripts_path}")
        print(f"Path exists: {os.path.exists(scripts_path)}")
        raise
    
    # retrieve the relevant chunks from the embeddings
    results = vector_search(query, embedded_chunks, top_k=top_k)
    
    # Faster context construction
    context_parts = []
    for i, result in enumerate(results):
        chunk_text = result['chunk']['text']
        source = result['chunk']['metadata']['source']
        
        # Shorter chunks for faster processing
        clean_text = chunk_text.strip()
        if len(clean_text) > 250:
            clean_text = clean_text[:250] + "..."
        
        context_parts.append(f"[{source}] {clean_text}")
    
    if not context_parts:
        return "I couldn't find relevant information to answer your question."
    
    context = "\n\n".join(context_parts)
    
    # Shorter, simpler prompt
    prompt = f"""Documents:
{context}

Question: {query}

Answer based on the documents:"""
    
    return llm.generate_response(prompt, max_new_tokens=40, temperature=0.1)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG system with local LLM')
    parser.add_argument('--embeddings', '-e', default='./chunked_corpus/embedded_chunks.pkl',
                        help='Path to the embedded chunks pickle file')
    parser.add_argument('--model', '-m', default='TinyLlama/TinyLlama-1.1B-Chat-v1.0',
                        help='Hugging Face model to use')
    parser.add_argument('--device', '-d', choices=['cpu', 'cuda', 'mps'], 
                        help='Device to run the model on (default: auto-detect)')
    parser.add_argument('--query', '-q', help='Query to test the RAG system')
    parser.add_argument('--interactive', '-i', action='store_true', 
                        help='Run in interactive mode')
    
    args = parser.parse_args()
    
    embedded_chunks = load_embedded_chunks(args.embeddings)
    if embedded_chunks is None:
        return
    
    llm = LocalLLM(model_name=args.model, device=args.device)
    
    if args.query:
        response = rag_response(args.query, embedded_chunks, llm)
        print(f"\nQuery: {args.query}")
        print(f"\nResponse: {response}")
    
    if args.interactive or not args.query:
        print("\nEntering interactive mode. Type 'exit' to quit.")
        while True:
            query = input("\nEnter your question: ")
            if query.lower() in ['exit', 'quit', 'q']:
                break
            
            response = rag_response(query, embedded_chunks, llm)
            print(f"\nResponse: {response}")

if __name__ == "__main__":
    main() 