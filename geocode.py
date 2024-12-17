import requests
import time
import csv
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Your Google Maps Geocoding API key
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')  # Correct usage
print(f"Loaded API Key: {API_KEY}")  # Debugging statement (remove after verification)

# Input and output file paths
INPUT_FILE = 'addresses.txt'
OUTPUT_FILE = 'addresses_with_coords.csv'

def read_addresses(file_path):
    with open(file_path, 'r') as file:
        addresses = [line.strip() for line in file if line.strip()]
    return addresses

def geocode_address(address, api_key):
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': address,
        'key': api_key
    }
    try:
        response = requests.get(base_url, params=params)
        print(f"Request URL: {response.url}")  # Debugging statement
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} for address: {address}")
            return None, None
        data = response.json()
        print(f"Response Status: {data['status']}")  # Debugging statement
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            print(f"Geocoding failed for address: {address}, Status: {data['status']}")
            return None, None
    except Exception as e:
        print(f"Exception occurred for address: {address}, Error: {e}")
        return None, None

def write_results(addresses, coords, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['Address', 'Latitude', 'Longitude']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for address, (lat, lng) in zip(addresses, coords):
            writer.writerow({
                'Address': address,
                'Latitude': lat if lat is not None else '',
                'Longitude': lng if lng is not None else ''
            })

def main():
    addresses = read_addresses(INPUT_FILE)
    print(f"Total addresses to geocode: {len(addresses)}")  # Debugging statement
    coords = []
    for address in addresses:
        lat, lng = geocode_address(address, API_KEY)
        coords.append((lat, lng))
        time.sleep(0.1)  # To respect API rate limits
    write_results(addresses, coords, OUTPUT_FILE)
    print(f"Geocoding complete. Results saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
