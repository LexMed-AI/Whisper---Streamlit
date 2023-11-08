import streamlit as st
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

st.title('SSD Hearing Transcription')

uploaded_file = st.file_uploader("Upload your OGG audio file", type=['ogg'])

if uploaded_file is not None:
    m = MultipartEncoder(
        fields={
            'file': (uploaded_file.name, uploaded_file, 'application/ogg'),
            'model': 'whisper-1'
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

    if response.status_code == 200:
        st.write("Transcription completed successfully!")
        transcription = response.json()['text']
        st.text_area("Transcription", transcription)
    else:
        st.error("Failed to transcribe audio. Please try again.")
