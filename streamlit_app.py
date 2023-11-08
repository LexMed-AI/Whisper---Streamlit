import streamlit as st
import requests
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

st.title('SSD Hearing Transcription')

# Define the function to convert the SRT text to a PDF
def srt_to_pdf(srt_text, file_name):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setTitle(file_name)
    
    # Start from the top and reduce y coordinate every new line
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
    m = MultipartEncoder(
        fields={
            'file': (uploaded_file.name, uploaded_file, 'application/ogg'),
            'model': 'whisper-1',
            'response_format': 'srt'  # Request timestamps in SRT format
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

    # Debugging steps start here
    # Print out the raw response content for debugging
    st.write("Raw response content:", response.text)

    # Check the response status code before parsing as JSON
    if response.status_code != 200:
        # Print the error to the Streamlit interface
        st.error(f"Failed to transcribe audio. Status code: {response.status_code}. Response text: {response.text}")
        # Stop further execution of the script
        st.stop()
    else:
        # Try to parse the JSON response and extract the transcription text
        try:
            srt_transcription = response.json()['text']
            
            # Call the function to convert the SRT text to a PDF
            pdf_file_buffer = srt_to_pdf(srt_transcription, 'Transcription.pdf')
            
            # Let the user download the PDF
            st.download_button(
                label="Download Transcript as PDF",
                data=pdf_file_buffer,
                file_name='Transcription.pdf',
                mime='application/pdf'
            )
        except json.JSONDecodeError:
            st.error("Failed to parse the response as JSON.")
            st.text(response.text)
            # Stop further execution of the script
            st.stop()
