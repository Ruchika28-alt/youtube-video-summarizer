import streamlit as st
import google.generativeai as genai
import requests
import json
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Streamlit page setup
st.set_page_config(page_title="YouTube Video Summarizer", layout="wide")
st.title("🎥 YouTube Video Summarizer")

# Sidebar inputs
google_api_key = st.sidebar.text_input("Enter your Google API Key:", type="password")
youtube_api_key = st.sidebar.text_input("Enter your YouTube Data API Key:", type="password")
youtube_link = st.sidebar.text_input("Enter YouTube Video Link:")
summary_length = st.sidebar.select_slider("Select Summary Length:", options=['Short', 'Medium', 'Long'], value='Medium')

# Helper: Extract video ID
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        return None

# Fetch transcript using YouTube Data API v3
def get_youtube_transcript(video_id, api_key):
    try:
        # Get caption tracks
        url = f"https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId={video_id}&key={api_key}"
        response = requests.get(url)
        data = response.json()

        if "items" not in data or len(data["items"]) == 0:
            st.error("No captions available for this video.")
            return None

        caption_id = data["items"][0]["id"]

        # Download caption text
        caption_url = f"https://www.googleapis.com/youtube/v3/captions/{caption_id}?tfmt=ttml&key={api_key}"
        caption_response = requests.get(caption_url)

        if caption_response.status_code != 200:
            st.error("Failed to retrieve captions.")
            return None

        # Extract text from XML/TTML captions
        from xml.etree import ElementTree as ET
        root = ET.fromstring(caption_response.text)
        transcript = " ".join([elem.text for elem in root.iter() if elem.text])
        return transcript

    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

# Generate summary with Gemini
def generate_summary(transcript, length, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"You are a YouTube video summarizer. Provide a {length.lower()} summary with key points in under 1500 words:\n\n"
        response = model.generate_content(prompt + transcript)
        return response.text
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return None

# Create PDF
def create_pdf(summary_text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(72, 800, "YouTube Video Summary")
    text = c.beginText(40, 780)
    text.setFont("Helvetica", 12)
    for line in summary_text.split('\n'):
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# Main logic
if youtube_link:
    video_id = extract_video_id(youtube_link)
    if video_id:
        thumbnail = f"https://img.youtube.com/vi/{video_id}/0.jpg"
        st.image(thumbnail, caption="Video Thumbnail", use_container_width=True)

if google_api_key and youtube_api_key and youtube_link and st.button("Generate Summary"):
    video_id = extract_video_id(youtube_link)
    transcript = get_youtube_transcript(video_id, youtube_api_key)
    if transcript:
        st.success("Transcript retrieved successfully!")
        summary = generate_summary(transcript, summary_length, google_api_key)
        if summary:
            st.subheader("📝 Detailed Summary")
            st.write(summary)
            pdf_bytes = create_pdf(summary)
            st.download_button("Download Summary as PDF", data=pdf_bytes, file_name="YouTube_Summary.pdf", mime="application/pdf")
        else:
            st.error("Failed to generate summary.")
    else:
        st.error("Transcript not available or could not be retrieved.")

