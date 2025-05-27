import os
import argparse
import re
import json
import nltk
from typing import List, Dict, Any
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def read_text_file(file_path: str) -> str:
    # read text content from a file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def semantic_chunk_text(text: str, max_chunk_size: int = 1000) -> List[str]:
    # split text into semantic chunks based on sentences and paragraphs.
    # tries to keep related content together while respecting max_chunk_size.
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # if paragraph is already too large, split it into sentences
        if len(paragraph) > max_chunk_size:
            sentences = sent_tokenize(paragraph)
            
            for sentence in sentences:
                # if adding this sentence would exceed max size, start a new chunk
                if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    # add a space if the current chunk isn't empty
                    if current_chunk:
                        current_chunk += " "
                    current_chunk += sentence
        else:
            # if adding this paragraph would exceed max size, start a new chunk
            if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # add a newline if the current chunk isn't empty
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph
    
    if current_chunk:
        chunks.append(current_chunk)
    
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

def process_file(file_path: str, output_dir: str, max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
    # process a single text file into semantic chunks with metadata
    text = read_text_file(file_path)
    if not text:
        return []
    
    chunks = semantic_chunk_text(text, max_chunk_size)
    metadata = create_metadata(file_path)
    
    chunk_documents = []
    for i, chunk_content in enumerate(chunks):
        word_count = len(word_tokenize(chunk_content))
        
        chunk_doc = {
            "chunk_id": f"{metadata['title']}_semantic_chunk_{i}",
            "text": chunk_content,
            "metadata": {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "word_count": word_count,
                "chunking_method": "semantic"
            }
        }
        chunk_documents.append(chunk_doc)
    
    # save chunks to output directory
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{metadata['title']}_semantic_chunks.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunk_documents, f, indent=2)
    
    print(f"Processed {file_path} into {len(chunks)} semantic chunks. Saved to {output_path}")
    return chunk_documents

def process_directory(input_dir: str, output_dir: str, max_chunk_size: int = 1000) -> List[Dict[str, Any]]:
    # process all text files in a directory
    all_chunks = []
    
    # create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # process each text file in the directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_dir, filename)
            chunks = process_file(file_path, output_dir, max_chunk_size)
            all_chunks.extend(chunks)
    
    # save all chunks to a single file
    if all_chunks:
        all_chunks_path = os.path.join(output_dir, "all_semantic_chunks.json")
        with open(all_chunks_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=2)
        print(f"Saved all {len(all_chunks)} semantic chunks to {all_chunks_path}")
    
    return all_chunks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Split text files into semantic chunks for RAG system')
    parser.add_argument('--input', '-i', help='Input text file or directory', required=True)
    parser.add_argument('--output', '-o', help='Output directory for chunks', default='chunked_corpus')
    parser.add_argument('--max-chunk-size', '-c', type=int, help='Maximum chunk size in characters', default=1000)
    args = parser.parse_args()

    if os.path.isdir(args.input):
        process_directory(args.input, args.output, args.max_chunk_size)
    elif os.path.isfile(args.input):
        process_file(args.input, args.output, args.max_chunk_size)
    else:
        print(f"Input path {args.input} does not exist") 