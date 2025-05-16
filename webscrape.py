import requests
import fitz
import os
import time
import json
import urllib.parse
from bs4 import BeautifulSoup

def download_pdf(url, output_dir="raw_corpus", max_retries=3, timeout=30):
    # extract filename from URL
    filename = os.path.basename(urllib.parse.urlparse(url).path)
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    # skip if already exists
    base, ext = os.path.splitext(filename)
    compressed_path = os.path.join(output_dir, f"{base}_compressed{ext}")
    if os.path.exists(compressed_path):
        print(f"Compressed version already exists at {compressed_path}, skipping download")
        return None
    
    print(f"Downloading PDF from {url}...")
    print(f"Will save as {output_path}")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status() 
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
def compress_pdf(input_path, output_dir="raw_corpus", dpi=50, delete_original=True):
    if not os.path.exists(input_path):
        print(f"Input file {input_path} not found.")
        return None
    
    # create compressed filename with same name but _compressed suffix
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
        
        # Delete original file if requested
        if delete_original:
            os.remove(input_path)
            print(f"Deleted original file {input_path}")
        
        return output_path
        
    except Exception as e:
        print(f"Error compressing PDF: {e}")
        return None

def get_pdf_links_for_year(year):
    # scrape the Phillipian archives page for a specific year and extract all PDF links.
    
    archive_url = f"https://archives.phillipian.net/explore?year={year}"
    pdf_links = []
    
    try:
        print(f"Fetching archive page for year {year}...")
        response = requests.get(archive_url)
        response.raise_for_status()
        
        # parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        # print(soup)
        # find all links that point to PDFs
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith(f"http://pdf.phillipian.net/{year}/") and href.endswith('.pdf'):
                pdf_links.append(href)
            # Also check for relative links
            elif href.startswith(f"/{year}/") and href.endswith('.pdf'):
                pdf_links.append(f"http://pdf.phillipian.net{href}")
        
        print(f"Found {len(pdf_links)} PDF links for year {year}")
        return pdf_links
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching archive page: {e}")
        return []

def process_year(year, download_dir="raw_corpus"):
    # process all PDFs for a given year - download and compress each one.
    
    pdf_links = get_pdf_links_for_year(year)
    
    if not pdf_links:
        print(f"No PDF links found for year {year}")
        return
    
    for i, url in enumerate(pdf_links):
        print(f"Processing PDF {i+1}/{len(pdf_links)}: {url}")
        
        original_path = download_pdf(url, output_dir=download_dir)
        if original_path:
            compressed_path = compress_pdf(original_path, output_dir=download_dir, delete_original=True)
        if i < len(pdf_links) - 1:
            time.sleep(2)

if __name__ == "__main__":
    years_to_process = ["2025", "2024"]
    
    for year in years_to_process:
        process_year(year)
