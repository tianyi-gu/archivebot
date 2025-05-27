import argparse
import os
from rag_app.llm_interface import LocalLLM, load_embedded_chunks, rag_response

def main():
    parser = argparse.ArgumentParser(description='ArchiveBot: RAG system for archived materials')
    parser.add_argument('--embeddings', '-e', default='./chunked_corpus/embedded_chunks.pkl',
                        help='Path to the embedded chunks pickle file')
    parser.add_argument('--model', '-m', default='TinyLlama/TinyLlama-1.1B-Chat-v1.0',
                        help='Hugging Face model to use')
    parser.add_argument('--device', '-d', choices=['cpu', 'cuda', 'mps'], 
                        help='Device to run the model on (default: auto-detect)')
    parser.add_argument('--top-k', '-k', type=int, default=3,
                        help='Number of chunks to retrieve for each query')
    
    args = parser.parse_args()
    
    # check if embeddings file exists
    if not os.path.exists(args.embeddings):
        print(f"Error: Embeddings file {args.embeddings} not found.")
        print("Please run the embedding generation script first:")
        print("python embed_chunks.py --input ./chunked_corpus/all_chunks.json --output ./chunked_corpus/embedded_chunks.pkl")
        return
    
    # load embedded chunks
    print(f"Loading embeddings from {args.embeddings}...")
    embedded_chunks = load_embedded_chunks(args.embeddings)
    if embedded_chunks is None:
        return
    
    # initialize LLM
    print(f"initializing LLM with model {args.model}...")
    llm = LocalLLM(model_name=args.model, device=args.device)
    
    # interactive mode
    print("\n" + "="*50)
    print("Welcome to ArchiveBot!")
    print("Ask questions about the archived materials from the Oliver Wendell Holmes Library (OWHL).")
    print("Type 'exit' to quit.")
    print("="*50 + "\n")
    
    while True:
        query = input("Your question: ")
        if query.lower() in ['exit', 'quit', 'q']:
            break
        
        print("\nSearching for relevant information...")
        response = rag_response(query, embedded_chunks, llm, top_k=args.top_k)
        print(f"\nArchiveBot: {response}\n")

if __name__ == "__main__":
    main() 