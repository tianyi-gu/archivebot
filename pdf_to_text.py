import os
import argparse
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

# extracts text from a pdf file using OCR and saves it to a text file (taking in a file path and optional output path)

def pdf_to_text(pdf_path, output_path=None):
    
    # If output path is not specified, create one based on the PDF filename
    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + '.txt'
    
    print(f"Converting {pdf_path} to text...")
    
    # Convert PDF to images
    try:
        poppler_path = "/opt/homebrew/bin"
        
        pages = convert_from_path(pdf_path, poppler_path=poppler_path)
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return None
    
    # Extract text from each page
    full_text = ""
    for i, page in enumerate(pages):
        print(f"Processing page {i+1}/{len(pages)}...")
        text = pytesseract.image_to_string(page)
        full_text += text + "\n\n"
    
    # Write text to output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"Text successfully saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error writing to output file: {e}")
        return None


parser = argparse.ArgumentParser(description='Convert PDF to text using OCR')
parser.add_argument('pdf_path', help='Path to the PDF file')
parser.add_argument('-o', '--output', help='Path to save the output text file')
args = parser.parse_args()

pdf_to_text(args.pdf_path, args.output)
