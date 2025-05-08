import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import argparse
from typing import List, Dict, Any
import pickle

def load_chunks(file_path: str) -> List[Dict[str, Any]]:
    # load chunks from a JSON file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading chunks from {file_path}: {e}")
        return []

def generate_embeddings(chunks: List[Dict[str, Any]], model_name: str = 'all-MiniLM-L6-v2') -> Dict[str, Any]:
    # generate embeddings for each chunk using SentenceTransformers
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    
    print(f"Generating embeddings for {len(chunks)} chunks...")
    texts = [chunk['text'] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # create a dictionary with both chunks and their embeddings
    embedded_chunks = {
        "chunks": chunks,
        "embeddings": embeddings,
        "model_name": model_name
    }
    
    return embedded_chunks

def save_embeddings(embedded_chunks: Dict[str, Any], output_path: str):
    # save the embedded chunks to a pickle file
    try:
        with open(output_path, 'wb') as f:
            pickle.dump(embedded_chunks, f)
        print(f"Embeddings saved to {output_path}")
    except Exception as e:
        print(f"Error saving embeddings to {output_path}: {e}")

def vector_search(query: str, embedded_chunks: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
    # search for the most similar chunks to a query
    model = SentenceTransformer(embedded_chunks["model_name"])
    query_embedding = model.encode(query)
    
    # calculate cosine similarity
    embeddings = np.array(embedded_chunks["embeddings"])
    similarities = np.dot(embeddings, query_embedding) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # get top k indices
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    # return top k chunks with their similarity scores
    results = []
    for idx in top_indices:
        results.append({
            "chunk": embedded_chunks["chunks"][idx],
            "similarity": float(similarities[idx])
        })
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for text chunks')
    parser.add_argument('--input', '-i', default='./chunked_corpus/all_chunks.json', 
                        help='Input JSON file containing chunks')
    parser.add_argument('--output', '-o', default='./chunked_corpus/embedded_chunks.pkl',
                        help='Output pickle file for embeddings')
    parser.add_argument('--model', '-m', default='all-MiniLM-L6-v2',
                        help='SentenceTransformer model to use')
    parser.add_argument('--query', '-q', 
                        help='Optional query to test search functionality')
    parser.add_argument('--top-k', '-k', type=int, default=3,
                        help='Number of top results to return for query')
    
    args = parser.parse_args()
    
    # create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    chunks = load_chunks(args.input)
    if not chunks:
        return
    
    embedded_chunks = generate_embeddings(chunks, args.model)
    
    save_embeddings(embedded_chunks, args.output)
    
    # test search if query is provided
    if args.query:
        print(f"\nTesting search with query: '{args.query}'")
        results = vector_search(args.query, embedded_chunks, args.top_k)
        
        print(f"\nTop {args.top_k} results:")
        for i, result in enumerate(results):
            print(f"\n{i+1}. Similarity: {result['similarity']:.4f}")
            print(f"   Chunk ID: {result['chunk']['chunk_id']}")
            print(f"   Date: {result['chunk']['metadata']['date']}")
            print(f"   Source: {result['chunk']['metadata']['source']}")
            print(f"   Full Text:")
            print("   " + result['chunk']['text'].replace('\n', '\n   '))
            print("-" * 80)

if __name__ == "__main__":
    main() 