import os
import argparse
import re
import json
from typing import List, Dict, Any

def read_text_file(file_path: str) -> str:
    # read text content from a file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    # split text into overlapping chunks of specified size
   
    chunks = []
    start = 0
    
    while start < len(text):
        # Take a chunk of size chunk_size
        end = start + chunk_size
        
        # If we're not at the beginning, back up by overlap characters
        if start > 0:
            start -= overlap
            
        # Get the chunk
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move to the next chunk
        start = end
    
    return chunks

def create_metadata(file_path: str) -> Dict[str, Any]:
    # create metadata for the document
    filename = os.path.basename(file_path)
    base_name, _ = os.path.splitext(filename)
    
    # extract date if it's in the filename (assuming format like 04182025.txt)
    date_match = re.search(r'(\d{2})(\d{2})(\d{4})', base_name)
    if date_match:
        month, day, year = date_match.groups()
        date = f"{year}-{month}-{day}"
    else:
        date = "unknown"
    
    return {
        "source": filename,
        "date": date,
        "title": base_name,
        "file_path": file_path
    }

def process_file(file_path: str, output_dir: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    # process a single text file into chunks with metadata
    text = read_text_file(file_path)
    if not text:
        return []
    
    chunks = chunk_text(text, chunk_size, overlap)
    metadata = create_metadata(file_path)
    
    chunk_documents = []
    for i, chunk_content in enumerate(chunks):
        chunk_doc = {
            "chunk_id": f"{metadata['title']}_chunk_{i}",
            "text": chunk_content,
            "metadata": {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        }
        chunk_documents.append(chunk_doc)
    
    # save chunks to output directory
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{metadata['title']}_chunks.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunk_documents, f, indent=2)
    
    print(f"Processed {file_path} into {len(chunks)} chunks. Saved to {output_path}")
    return chunk_documents

def process_directory(input_dir: str, output_dir: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    # process all text files in a directory
    all_chunks = []
    
    # create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # process each text file in the directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_dir, filename)
            chunks = process_file(file_path, output_dir, chunk_size, overlap)
            all_chunks.extend(chunks)
    
    # save all chunks to a single file
    if all_chunks:
        all_chunks_path = os.path.join(output_dir, "all_chunks.json")
        with open(all_chunks_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=2)
        print(f"Saved all {len(all_chunks)} chunks to {all_chunks_path}")
    
    return all_chunks


parser = argparse.ArgumentParser(description='Split text files into chunks for RAG system')
parser.add_argument('--input', '-i', help='Input text file or directory', required=True)
parser.add_argument('--output', '-o', help='Output directory for chunks', default='chunked_corpus')
parser.add_argument('--chunk-size', '-c', type=int, help='Target chunk size in characters', default=1000)
parser.add_argument('--overlap', type=int, help='Overlap between chunks in characters', default=200)
args = parser.parse_args()

if os.path.isdir(args.input):
    process_directory(args.input, args.output, args.chunk_size, args.overlap)
elif os.path.isfile(args.input):
    process_file(args.input, args.output, args.chunk_size, args.overlap)
else:
    print(f"Input path {args.input} does not exist") 