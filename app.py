import streamlit as st
import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv
from io import StringIO

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from environment variables
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Function to geocode a single address
def geocode_address(address, api_key):
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': address,
        'key': api_key
    }
    try:
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            st.error(f"Error: Received status code {response.status_code} for address: {address}")
            return None, None
        data = response.json()
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            st.warning(f"Geocoding failed for address: {address}, Status: {data['status']}")
            return None, None
    except Exception as e:
        st.error(f"Exception occurred for address: {address}, Error: {e}")
        return None, None

# Streamlit App
def main():
    st.title("Batch Geocoding Application")
    st.write("Upload a CSV or TXT file with addresses to geocode.")

    # File uploader accepts CSV or TXT files
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "txt"])

    if uploaded_file is not None:
        try:
            # Determine file type and read accordingly
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
                # Assume addresses are in the first column
                address_column = df.columns[0]
                addresses = df[address_column].dropna().tolist()
            else:
                # Read TXT file
                data = StringIO(uploaded_file.getvalue().decode("utf-8"))
                addresses = [line.strip() for line in data if line.strip()]
            
            st.success(f"Successfully loaded {len(addresses)} addresses.")
            st.write("Preview of addresses:")
            st.write(pd.DataFrame(addresses, columns=['Address']).head())

            if st.button("Run Geocoding"):
                if API_KEY is None:
                    st.error("API Key not found. Please ensure it's set in the `.env` file.")
                    return

                st.info("Starting geocoding process...")
                geocoded_data = []
                for idx, address in enumerate(addresses, start=1):
                    lat, lng = geocode_address(address, API_KEY)
                    geocoded_data.append({
                        'Address': address,
                        'Latitude': lat,
                        'Longitude': lng
                    })
                    st.progress(idx / len(addresses))
                    time.sleep(0.1)  # To respect API rate limits

                # Create DataFrame from results
                result_df = pd.DataFrame(geocoded_data)
                st.success("Geocoding complete.")
                st.write(result_df)

                # Provide download link
                csv = result_df.to_csv(index=False)
                st.download_button(
                    label="Download Geocoded Data as CSV",
                    data=csv,
                    file_name='addresses_with_coords.csv',
                    mime='text/csv',
                )

        except Exception as e:
            st.error(f"Error processing file: {e}")

if __name__ == '__main__':
    main()
