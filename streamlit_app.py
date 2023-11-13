import streamlit as st
from PIL import Image
from io import BytesIO
import zipfile
import os
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
        if '-->' in line:  # Identify timestamp lines
            timestamp = line.strip()
            processed_text += f"[{timestamp}] "  # Add timestamp to the transcript
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

# Function to extract metadata from zip file
def extract_metadata(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        metadata_file = [f for f in zip_ref.namelist() if f.endswith('.json')]
        if metadata_file:
            metadata_content = zip_ref.read(metadata_file[0])
            return json.loads(metadata_content)
        else:
            return None

# Streamlit file uploader
uploaded_file = st.file_uploader("Upload your Zip or OGG audio file", type=['zip', 'ogg'])

# Rest of the code for file processing
# ...

# Example usage (within the appropriate section of the file processing code)
if uploaded_file is not None and uploaded_file.name.endswith('.ogg'):
    # Process OGG file
    # ...
    srt_transcription = response.json()['text']
    metadata = {
        "claimant_name": "John Doe",
        "judge_name": "Jane Smith",
        "appearances": ["John Doe Claimant", "Jane Lawyer Attorney for Claimant", "Alex Expert Vocational Expert"]
    }
    srt_transcription_processed = add_speaker_labels_and_metadata(srt_transcription, metadata)
    pdf_file_buffer = srt_to_pdf(srt_transcription_processed, 'Transcription.pdf')
    # ...



# Function to convert SRT text to PDF
def srt_to_pdf(srt_text, file_name):
   def srt_to_pdf(srt_text, file_name):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setTitle(file_name)
     
y_position = 750
for line in srt_text.split('\\n'):
    if not line.strip().isdigit() and line.strip() != '':
        c.drawString(72, y_position, line)
        y_position -= 15
        if y_position < 72:
            y_position = 750
            c.showPage()

c.save()
pdf_buffer.seek(0)
return pdf_buffer

```

# Function to extract metadata from zip file
def extract_metadata(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        # Assuming metadata is in a JSON file inside the zip
        metadata_file = [f for f in zip_ref.namelist() if f.endswith('.json')]
        if metadata_file:
            metadata_content = zip_ref.read(metadata_file[0])
            return json.loads(metadata_content)
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
            url='https://api.openai.com/v1/audio/transcriptions',
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
