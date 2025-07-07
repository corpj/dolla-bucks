#!/usr/bin/env python3
import csv
import os
import requests
from datetime import datetime
from urllib.parse import urlparse
import time

def download_images_from_csv(csv_file):
    # Create timestamped folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"/home/corpj/projects/dolla-bucks/Inventory/images_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    # Read CSV and download images
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        
        total_images = 0
        successful_downloads = 0
        failed_downloads = 0
        
        for row in reader:
            if row and row[0]:  # Check if URL exists
                url = row[0].strip()
                if url.startswith('http'):
                    total_images += 1
                    
                    # Extract filename from URL
                    parsed_url = urlparse(url)
                    filename = os.path.basename(parsed_url.path)
                    
                    # Download image
                    try:
                        print(f"Downloading {filename}...")
                        response = requests.get(url, timeout=30)
                        response.raise_for_status()
                        
                        # Save image
                        output_path = os.path.join(output_dir, filename)
                        with open(output_path, 'wb') as img_file:
                            img_file.write(response.content)
                        
                        successful_downloads += 1
                        print(f"  ✓ Saved: {filename}")
                        
                        # Small delay to be respectful to the server
                        time.sleep(0.5)
                        
                    except requests.exceptions.RequestException as e:
                        failed_downloads += 1
                        print(f"  ✗ Failed to download {filename}: {str(e)}")
                    except Exception as e:
                        failed_downloads += 1
                        print(f"  ✗ Unexpected error for {filename}: {str(e)}")
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"Download Summary:")
        print(f"  Total images: {total_images}")
        print(f"  Successful: {successful_downloads}")
        print(f"  Failed: {failed_downloads}")
        print(f"  Output directory: {output_dir}")
        print(f"{'='*50}")

if __name__ == "__main__":
    csv_file = "/home/corpj/projects/dolla-bucks/Inventory/csv/imageURLs_download_2025-06-30.csv"
    download_images_from_csv(csv_file)