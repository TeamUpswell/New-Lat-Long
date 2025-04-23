import os
import requests
from dotenv import load_dotenv
import time
import csv
import logging

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('AIzaSyC2OGAg70_9hBf-9uE1iAFxbrA4mikYxoM')

# Configure logging
logging.basicConfig(
    filename='geocoding.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def geocode_address(address, api_key):
    """
    Geocode an address using Google Maps Geocoding API.

    Args:
        address (str): The address to geocode.
        api_key (str): Your Google Maps API key.

    Returns:
        tuple: (latitude, longitude) if successful, None otherwise.
    """
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        geocode_data = response.json()
        
        if geocode_data['status'] == 'OK':
            location = geocode_data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        elif geocode_data['status'] == 'ZERO_RESULTS':
            logging.warning(f"No results found for address: {address}")
            print(f"No results found for address: {address}")
        elif geocode_data['status'] == 'OVER_QUERY_LIMIT':
            logging.error("Over query limit. Waiting for 2 seconds before retrying...")
            print("Over query limit. Waiting for 2 seconds before retrying...")
            time.sleep(2)
            return geocode_address(address, api_key)  # Recursive retry
        else:
            logging.error(f"Error geocoding address '{address}': {geocode_data['status']}")
            print(f"Error geocoding address '{address}': {geocode_data['status']}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception for address '{address}': {e}")
        print(f"Request exception for address '{address}': {e}")
    return None

def geocode_addresses_from_text(input_file, output_file, api_key):
    """
    Geocode addresses from an input text file and write results to an output CSV file.

    Args:
        input_file (str): Path to the input text file containing addresses.
        output_file (str): Path to the output CSV file to write geocoded results.
        api_key (str): Your Google Maps API key.
    """
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        writer = csv.writer(outfile)
        writer.writerow(['Address', 'Latitude', 'Longitude'])  # CSV Header
        
        for line_number, line in enumerate(infile, start=1):
            address = line.strip()
            if not address:
                logging.info(f"Skipping blank line at line number {line_number}.")
                print(f"Skipping blank line at line number {line_number}.")
                continue  # Skip blank lines
            
            coords = geocode_address(address, api_key)
            if coords:
                writer.writerow([address, coords[0], coords[1]])
                logging.info(f"{address} => Latitude: {coords[0]}, Longitude: {coords[1]}")
                print(f"{address} => Latitude: {coords[0]}, Longitude: {coords[1]}")
            else:
                writer.writerow([address, 'N/A', 'N/A'])
                logging.warning(f"Failed to geocode address: {address}")
                print(f"Failed to geocode address: {address}")
            
            time.sleep(0.1)  # To respect rate limits

if __name__ == "__main__":
    input_text_file = 'addresses.txt'          # Ensure this file exists in your project directory
    output_csv_file = 'geocoded_addresses.csv'
    geocode_addresses_from_text(input_text_file, output_csv_file, AIzaSyC2OGAg70_9hBf-9uE1iAFxbrA4mikYxoM)
