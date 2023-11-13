import streamlit as st
from PIL import Image
from io import BytesIO
import zipfile
import os
import json
from bs4 import BeautifulSoup  # Import BeautifulSoup for parsing HTML
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Load and display the logo

logo_image = Image.open('lexmed_logo.png')
st.image(logo_image, width=800)
st.title('Hearing Whisperer')

# Function to add speaker labels to the transcript

def add_speaker_labels(transcript):
    # [Existing code for add_speaker_labels remains unchanged]

# Function to convert SRT text to PDF

def srt_to_pdf(srt_text, file_name):
    # [Existing code for srt_to_pdf remains unchanged]

# Function to extract metadata from zip file

def extract_metadata_from_index(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        index_file = [f for f in zip_ref.namelist() if 'index.html' in f]
        if index_file:
            with zip_ref.open(index_file[0]) as file:
                soup = BeautifulSoup(file, 'html.parser')
                # Extract required metadata from the HTML
                # This needs to be adjusted based on the structure of your HTML file
                metadata = {}
                # Example: metadata['title'] = soup.title.string
                # Add more extraction logic as per your HTML structure
                return metadata
        else:
            return None

# Streamlit file uploader

uploaded_file = st.file_uploader("Upload your Zip or OGG audio file", type=['zip', 'ogg'])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.zip'):
        # Process Zip file
        metadata = extract_metadata(uploaded_file)
        if metadata:
            st.write("Metadata extracted:", metadata)
        else:
            st.error("No metadata file found in the zip.")

        # Assuming you need to extract an OGG file from the zip
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            ogg_files = [f for f in zip_ref.namelist() if f.endswith('.ogg')]
            if ogg_files:
                ogg_file_path = ogg_files[0]
                zip_ref.extract(ogg_file_path)
                audio_file = open(ogg_file_path, 'rb')
                # Process the OGG file (same as below)
                # [Insert OGG file processing code here]
                os.remove(ogg_file_path)  # Clean up extracted file
            else:
                st.error("No OGG audio file found in the zip.")

    elif uploaded_file.name.endswith('.ogg'):
        # Process OGG file directly
        file_content = uploaded_file.read()

        m = MultipartEncoder(
            fields={
                'file': (uploaded_file.name, file_content, 'application/ogg'),
                'model': 'whisper-1',
                'response_format': 'srt'
            }
        )

        headers = {
            'Authorization': f'Bearer {st.secrets["OPENAI_API_KEY"]}',
            'Content-Type': m.content_type
        }

        st.write("Processing the audio file...")

        response = requests.post(
            url='<https://api.openai.com/v1/audio/transcriptions>',
            data=m,
            headers=headers
        )

        if response.status_code != 200:
            st.error(f"Failed to transcribe audio. Status code: {response.status_code}. Response text: {response.text}")
        else:
            try:
                srt_transcription = response.json()['text']
                srt_transcription_labeled = add_speaker_labels(srt_transcription)
                pdf_file_buffer = srt_to_pdf(srt_transcription_labeled, 'Transcription.pdf')

                st.download_button(
                    label="Download Transcript as PDF",
                    data=pdf_file_buffer,
                    file_name='Transcription.pdf',
                    mime='application/pdf'
                )
                st.write("Transcription completed successfully!")
            except json.JSONDecodeError:
                st.error("Failed to parse the response as JSON.")
                st.text(response.text)

    else:
        st.error("Unsupported file format.")

# Example usage in your Streamlit file uploader section
if uploaded_file is not None:
    if uploaded_file.name.endswith('.zip'):
        # Process Zip file
        metadata = extract_metadata_from_index(uploaded_file)
        if metadata:
            st.write("Metadata extracted:", metadata)
        else:
            st.error("No index.html file found in the zip.")
        
        # [Continue with OGG file extraction and processing as before]
