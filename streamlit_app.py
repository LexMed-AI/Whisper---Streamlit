import streamlit as st
from PIL import Image
from io import BytesIO
import zipfile
import os
from bs4 import BeautifulSoup  # Import BeautifulSoup
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Load and display the logo
logo_image = Image.open('lexmed_logo.png')
st.image(logo_image, width=800)
st.title('Hearing Whisperer')

# Function to add speaker labels and metadata to the transcript
def add_speaker_labels_and_metadata(transcript, metadata):
    processed_text = f"Title: TRANSCRIPT of the Social Security Disability Hearing for {metadata['claimant_name']}\n"
    processed_text += f"Claimant: {metadata['claimant_name']}\n"
    processed_text += f"Administrative Law Judge: {metadata['judge_name']}\n"
    processed_text += f"Appearances: {', '.join(metadata['appearances'])}\n\n"
    
    # Add timestamps and process the rest of the transcript
    for line in transcript.split('\n'):
        if '-->' in line:
            timestamp = line.strip()
            processed_text += f"[{timestamp}] "
        else:
            processed_text += f"{line}\n"
    return processed_text

# Function to convert SRT text to PDF
def srt_to_pdf(srt_text, file_name):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setTitle(file_name)

    y_position = 750
    for line in srt_text.split('\n'):
        if not line.strip().isdigit() and line.strip() != '':
            c.drawString(72, y_position, line)
            y_position -= 15
            if y_position < 72:
                y_position = 750
                c.showPage()

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# Function to extract metadata from index.html inside a zip file
def extract_metadata_from_html(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        index_file = [f for f in zip_ref.namelist() if 'index.html' in f]
        if index_file:
            with zip_ref.open(index_file[0]) as file:
                soup = BeautifulSoup(file, 'html.parser')
                
                # Example of refined searches
                claimant_element = soup.find('div', {'id': 'claimant-info'})
                claimant = claimant_element.get_text().strip() if claimant_element else "Not Found"
                
                judge_element = soup.find('span', {'class': 'judge-name'})
                judge = judge_element.get_text().strip() if judge_element else "Not Found"
                
                hearing_date_element = soup.find('p', {'class': 'hearing-date'})
                hearing_date = hearing_date_element.get_text().strip() if hearing_date_element else "Not Found"

                metadata = {
                    "claimant_name": claimant,
                    "judge_name": judge,
                    "hearing_date": hearing_date,
                    # Additional fields
                }
                return metadata
        else:
            st.error("No index.html file found in the zip.")
            return None


# Streamlit file uploader
uploaded_file = st.file_uploader("Upload your Zip or OGG audio file", type=['zip', 'ogg'])

# Handling the uploaded file
if uploaded_file is not None:
    # Process Zip files
    if uploaded_file.name.endswith('.zip'):
        metadata = extract_metadata_from_html(uploaded_file)
        if metadata:
            st.write("Metadata extracted:", metadata)
            # Continue with additional processing for Zip files...
        else:
            st.error("Failed to extract metadata.")

    # Process OGG files
    elif uploaded_file.name.endswith('.ogg'):
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
            url='https://api.openai.com/v1/audio/transcriptions',
            data=m,
            headers=headers
        )

        if response.status_code != 200:
            st.error(f"Failed to transcribe audio. Status code: {response.status_code}. Response text: {response.text}")
        else:
            try:
                srt_transcription = response.json()['text']
                srt_transcription_processed = add_speaker_labels_and_metadata(srt_transcription, metadata)
                pdf_file_buffer = srt_to_pdf(srt_transcription_processed, 'Transcription.pdf')

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
