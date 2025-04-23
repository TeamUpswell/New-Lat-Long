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
                
                # Preview the dataframe first
                st.subheader("Preview of your data:")
                st.dataframe(df.head())
                
                # Then let user select which column contains addresses
                address_column = st.selectbox(
                    "Select the column containing addresses:",
                    options=df.columns.tolist()
                )
                
                # Only show addresses preview and geocoding button after column selection
                if st.button("Confirm Column Selection"):
                    addresses = df[address_column].dropna().tolist()
                    
                    st.success(f"Successfully loaded {len(addresses)} addresses from column '{address_column}'.")
                    st.write("Preview of addresses to geocode:")
                    st.write(pd.DataFrame(addresses, columns=['Address']).head())
                    
                    # Only show the geocoding button after confirmation
                    if st.button("Run Geocoding"):
                        process_geocoding(df, address_column, addresses)
            else:
                # Read TXT file
                data = StringIO(uploaded_file.getvalue().decode("utf-8"))
                addresses = [line.strip() for line in data if line.strip()]
                address_column = None  # No column selection for TXT files
                
                st.success(f"Successfully loaded {len(addresses)} addresses.")
                st.write("Preview of addresses to geocode:")
                st.write(pd.DataFrame(addresses, columns=['Address']).head())
                
                if st.button("Run Geocoding"):
                    process_geocoding(None, None, addresses, txt_mode=True)

        except Exception as e:
            st.error(f"Error processing file: {e}")
            st.exception(e)  # This will display the full traceback for debugging

def process_geocoding(df, address_column, addresses, txt_mode=False):
    """Helper function to handle the geocoding process."""
    if API_KEY is None:
        st.error("API Key not found. Please ensure it's set in the `.env` file.")
        return

    st.info("Starting geocoding process...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    if not txt_mode:
        # For CSV files, preserve the original DataFrame and add new columns
        result_df = df.copy()
        result_df['Latitude'] = None
        result_df['Longitude'] = None
        
        for idx, (index, row) in enumerate(df.iterrows()):
            address = row[address_column]
            if pd.notna(address):  # Skip NaN values
                lat, lng = geocode_address(address, API_KEY)
                result_df.at[index, 'Latitude'] = lat
                result_df.at[index, 'Longitude'] = lng
            
            # Update progress
            progress = (idx + 1) / len(df)
            progress_bar.progress(progress)
            status_text.text(f"Processing {idx+1} of {len(df)}: {address}")
            time.sleep(0.1)  # To respect API rate limits
    else:
        # For TXT files, create a new DataFrame
        geocoded_data = []
        for idx, address in enumerate(addresses, start=1):
            lat, lng = geocode_address(address, API_KEY)
            geocoded_data.append({
                'Address': address,
                'Latitude': lat,
                'Longitude': lng
            })
            
            # Update progress
            progress_bar.progress(idx / len(addresses))
            status_text.text(f"Processing {idx} of {len(addresses)}: {address}")
            time.sleep(0.1)  # To respect API rate limits
        
        result_df = pd.DataFrame(geocoded_data)

    status_text.text("Geocoding complete!")
    st.success("Geocoding complete.")
    st.subheader("Results:")
    st.dataframe(result_df)

    # Provide download link
    csv = result_df.to_csv(index=False)
    st.download_button(
        label="Download Geocoded Data as CSV",
        data=csv,
        file_name='addresses_with_coords.csv',
        mime='text/csv',
    )

if __name__ == '__main__':
    main()
