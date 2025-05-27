import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import pickle
from typing import List, Dict, Any

class LocalLLM:
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0", device=None): 
        print(f"Loading model: {model_name}")
        
        # auto-detect device if not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        
        self.device = device
        print(f"Using device: {device}")
        
        # load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # load in 8-bit quantization for memory efficiency if on CUDA
        if device == "cuda":
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                device_map="auto",
                load_in_8bit=True
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
        
        # create text generation 
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=device
        )
        
        print("Model loaded successfully")
    
    def generate_response(self, prompt, max_new_tokens=512, temperature=0.7):
        try:
            response = self.generator(
                prompt,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=0.95,
                num_return_sequences=1,
                truncation=True
            )
            
            # extract the generated text
            generated_text = response[0]['generated_text']
            
            # remove the prompt from the response
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
                
            return generated_text
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I encountered an error while generating a response."

def load_embedded_chunks(embeddings_path):
    try:
        with open(embeddings_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading embeddings from {embeddings_path}: {e}")
        return None

def rag_response(query, embedded_chunks, llm, top_k=3, max_context_length=3000):
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
    
    # construct the context from the retrieved chunks
    context = ""
    for i, result in enumerate(results):
        chunk_text = result['chunk']['text']
        source = result['chunk']['metadata']['source']
        date = result['chunk']['metadata']['date']
        
        # add chunk to context
        new_chunk = f"Document {i+1} (Source: {source}, Date: {date}):\n{chunk_text}\n\n"
        
        # check if adding this chunk would exceed max_context_length
        if len(context + new_chunk) > max_context_length:
            # truncate the chunk to fit within max_context_length
            available_space = max_context_length - len(context)
            if available_space > 100:
                new_chunk = new_chunk[:available_space] + "...\n\n"
                context += new_chunk
            break
        else:
            context += new_chunk
    
    # create prompt with context and query
    prompt = f"""Below are some relevant documents:

{context}

Based on the above documents, please answer the following question:
{query}

Answer:"""
    
    # generate response using the LLM
    return llm.generate_response(prompt)

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