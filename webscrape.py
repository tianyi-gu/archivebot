import requests
import fitz
import os
import time
import urllib.parse

def download_pdf(url, output_dir="raw_corpus", max_retries=3, timeout=30):
    # extract filename from URL
    filename = os.path.basename(urllib.parse.urlparse(url).path)
    
    # create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # full path for the output file
    output_path = os.path.join(output_dir, filename)
    
    print(f"Downloading PDF from {url}...")
    print(f"Will save as {output_path}")
    
    for attempt in range(max_retries):
        try:
            # set a timeout to avoid hanging
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status() 
            
            # save the file in chunks to handle large files better
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Successfully downloaded to {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Download failed.")
                return None

# compress the pdf
def compress_pdf(input_path, output_dir="raw_corpus", dpi=20):
    if not os.path.exists(input_path):
        print(f"Input file {input_path} not found.")
        return None
    
    # Create compressed filename with same name but _compressed suffix
    filename = os.path.basename(input_path)
    base, ext = os.path.splitext(filename)
    compressed_filename = f"{base}_compressed{ext}"
    output_path = os.path.join(output_dir, compressed_filename)
        
    try:
        print(f"Compressing PDF {input_path}...")
        input_pdf = fitz.open(input_path)
        output_pdf = fitz.open()

        for i, page in enumerate(input_pdf):
            print(f"Processing page {i+1}/{len(input_pdf)}...")
            # reduces image resolution and re-adds the page
            pix = page.get_pixmap(dpi=dpi)
            new_page = output_pdf.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, pixmap=pix)

        output_pdf.save(output_path, deflate=True)
        print(f"Compressed PDF saved as '{output_path}'")
        return output_path
        
    except Exception as e:
        print(f"Error compressing PDF: {e}")
        return None


url = "https://pdf.phillipian.net/2025/04182025.pdf"

# download the PDF
original_path = download_pdf(url)

# compress the PDF if download was successful
if original_path:
    compress_pdf(original_path)
