import streamlit as st
from PIL import Image
from io import BytesIO
import zipfile
from bs4 import BeautifulSoup
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import logging

# Setting up logging
log_file = 'whisper_script.log'
logging.basicConfig(filename=log_file, level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')

# Enhanced function to add speaker labels and metadata to the transcript
def enhanced_add_speaker_labels_and_metadata(transcript, metadata):
    try:
        processed_text = f"Title: TRANSCRIPT of the Social Security Disability Hearing for {metadata['claimant_name']}\n"
        processed_text += f"Claimant: {metadata['claimant_name']}\n"
        processed_text += f"Administrative Law Judge: {metadata['judge_name']}\n"
        processed_text += f"Appearances: {', '.join(metadata['appearances'])}\n\n"
        for line in transcript.split('\n'):
            if '-->' in line:
                timestamp = line.strip()
                processed_text += f"[{timestamp}] "
            else:
                processed_text += f"{line}\n"
        return processed_text
    except Exception as e:
        st.error(f"An error occurred while processing the transcript: {e}")
        logging.error(f"Transcript processing error: {e}")
        return None

# Function to prepare PDF content from SRT text
def prepare_pdf_content(srt_text):
    content = []
    current_page = []
    y_position = 750
    for line in srt_text.split('\n'):
        if not line.strip().isdigit() and line.strip() != '':
            current_page.append((line, y_position))
            y_position -= 15
            if y_position < 72:
                content.append(current_page)
                current_page = []
                y_position = 750
    if current_page:
        content.append(current_page)
    return content

# Function to generate PDF from prepared content
def generate_pdf_from_content(content, file_name):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setTitle(file_name)
    for page in content:
        for line, y_position in page:
            c.drawString(72, y_position, line)
        c.showPage()
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# Enhanced function to extract metadata from index.html inside a zip file
def enhanced_extract_metadata_from_html(zip_file):
    if not zipfile.is_zipfile(zip_file):
        st.error("The uploaded file is not a valid zip file.")
        return None
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            index_file = [f for f in zip_ref.namelist() if 'index.html' in f]
            if not index_file:
                st.error("No index.html file found in the zip.")
                return None
            with zip_ref.open(index_file[0]) as file:
                soup = BeautifulSoup(file, 'html.parser')
                claimant_element = soup.find('div', {'id': 'claimant-info'})
                judge_element = soup.find('span', {'class': 'judge-name'})
                hearing_date_element = soup.find('p', {'class': 'hearing-date'})
                claimant = claimant_element.get_text().strip() if claimant_element else "Not Found"
                judge = judge_element.get_text().strip() if judge_element else "Not Found"
                hearing_date = hearing_date_element.get_text().strip() if hearing_date_element else "Not Found"
                metadata = {
                    "claimant_name": claimant,
                    "judge_name": judge,
                    "hearing_date": hearing_date,
                    # Additional fields can be added here
                }
                return metadata
    except Exception as e:
        st.error(f"An error occurred while processing the zip file: {e}")
        logging.error(f"Zip file processing error: {e}")
        return None

# Enhanced function to process the OGG file
def enhanced_process_ogg_file(uploaded_file):
    try:
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
            headers=headers,
            timeout=60
        )

        if response.status_code == 200:
            try:
                return response.json()['text']
            except json.JSONDecodeError:
                logging.error(f"JSON parsing error. Response content: {response.text}")
                st.error("Failed to parse the response as JSON. Check logs for details.")
                return None
        else:
            st.error(f"Failed to transcribe audio. Status code: {response.status_code}. Response text: {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("The transcription request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        st.error(f"A network error occurred: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        logging.error(f"OGG file processing error: {e}")
        return None

# Main function of the script
def main():
    # Load and display the logo
    logo_image = Image.open('lexmed_logo.png')
    st.image(logo_image, width=800)
    st.title('Hearing Whisperer')

    # Streamlit file uploader
    uploaded_file = st.file_uploader("Upload your Zip or OGG audio file", type=['zip', 'ogg'])

    # Handling the uploaded file
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.zip'):
            metadata = enhanced_extract_metadata_from_html(uploaded_file)
            if metadata:
                st.write("Metadata extracted:", metadata)
                # Additional processing for Zip files...
            else:
                st.error("Failed to extract metadata.")
        elif uploaded_file.name.endswith('.ogg'):
            srt_transcription = enhanced_process_ogg_file(uploaded_file)
            if srt_transcription:
                srt_transcription_processed = enhanced_add_speaker_labels_and_metadata(srt_transcription, metadata)
                if srt_transcription_processed:
                    prepared_content = prepare_pdf_content(srt_transcription_processed)
                    pdf_file_buffer = generate_pdf_from_content(prepared_content, 'Transcription.pdf')
                    st.download_button(
                        label="Download Transcript as PDF",
                        data=pdf_file_buffer,
                        file_name='Transcription.pdf',
                        mime='application/pdf'
                    )
                    st.write("Transcription completed successfully!")
                else:
                    st.error("Failed to process the transcript.")
            else:
                st.error("Failed to process the audio file.")
        else:
            st.error("Unsupported file format.")

if __name__ == "__main__":
    main()
