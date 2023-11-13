import streamlit as st
from PIL import Image
import requests
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Load and display the logo
logo_image = Image.open('lexmed_logo.png')
st.image(logo_image, width=800)
st.title('Hearing Whisperer')

# Function to add speaker labels to the transcript
def add_speaker_labels(transcript):
    lines = transcript.split('\n')
    processed_lines = []
    speaker_cues = {
        "claimant": ["I believe", "My condition", "I cannot", "hurt"],
        "attorney": ["My client", "Objection", "No objections"],
        "ALJ": ["Hearing will come to order", "Please state your name", "What is your opinion", "Thank you"],
        "VE": ["In my professional opinion", "DOT Code", "Given these restrictions", "national economy"],
        "ME": ["Medically speaking", "From a medical standpoint"]
    }
    current_speaker = None
    for line in lines:
        for speaker, cues in speaker_cues.items():
            if any(cue in line for cue in cues):
                current_speaker = speaker
                break
        else:  # Continue to next line if no speaker cue found
            current_speaker = None
        if current_speaker:
            line = f"[{current_speaker.upper()}]: {line}"
        processed_lines.append(line)
    return '\n'.join(processed_lines)

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

# Streamlit file uploader
uploaded_file = st.file_uploader("Upload your OGG audio file", type=['ogg'])

if uploaded_file is not None:
    # Read the file content
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
            # Add labels to speakers in the transcript
            srt_transcription_labeled = add_speaker_labels(srt_transcription)
            pdf_file_buffer = srt_to_pdf(srt_transcription_labeled, 'Transcription.pdf')

            st.download_button(
                label="Download Transcript as PDF",
                data=pdf_buffer,
                file_name='Transcription.pdf',
                mime='application/pdf'
            )
            st.write("Transcription completed successfully!")
        except json.JSONDecodeError:
            st.error("Failed to parse the response as JSON.")
            st.text(response.text)
