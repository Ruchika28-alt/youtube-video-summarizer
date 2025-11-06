import re
import io
import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# -----------------------------
# Streamlit Page Configuration
# -----------------------------
st.set_page_config(page_title="YouTube Video Summarizer", layout="wide")

st.title("🎥 YouTube Video Summarizer")
st.write("Generate quick, clear, and downloadable summaries of any YouTube video using Google Gemini AI.")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("🧠 Configuration")
google_api_key = st.sidebar.text_input("Enter your Google API Key:", type="password")
youtube_link = st.sidebar.text_input("Enter YouTube Video Link:")

summary_length = st.sidebar.select_slider(
    "Select Summary Length:", options=['Short', 'Medium', 'Long'], value='Medium'
)

# -----------------------------
# Helper Functions
# -----------------------------
def get_video_id(url):
    """Extract YouTube video ID from different URL formats."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def extract_transcript_details(youtube_video_url):
    """Fetch and combine transcript text from a YouTube video."""
    try:
        video_id = get_video_id(youtube_video_url)
        if not video_id:
            st.error("Invalid YouTube URL. Please enter a valid link.")
            return None
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(segment["text"] for segment in transcript)
    except Exception as e:
        st.error(f"Transcript not available or could not be retrieved: {e}")
        return None

def generate_gemini_content(transcript_text, summary_length, api_key):
    """Generate summarized text using Google Gemini."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")

        prompt = f"""You are a professional summarizer.
        Based on the following YouTube transcript, create a {summary_length.lower()} summary.
        Focus on main ideas, structure, and clarity.
        Avoid unnecessary filler words or unrelated details.
        Transcript:
        """

        response = model.generate_content(prompt + transcript_text)
        return response.text.strip()
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return None

def create_pdf(summary_text):
    """Generate a downloadable PDF of the summary."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    text_obj = c.beginText(50, height - 50)
    text_obj.setFont("Helvetica", 11)

    for line in summary_text.splitlines():
        if text_obj.getY() <= 50:  # start new page if near bottom
            c.drawText(text_obj)
            c.showPage()
            text_obj = c.beginText(50, height - 50)
            text_obj.setFont("Helvetica", 11)
        text_obj.textLine(line)

    c.drawText(text_obj)
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# -----------------------------
# Main App Workflow
# -----------------------------
if youtube_link:
    video_id = get_video_id(youtube_link)
    if video_id:
        video_thumbnail = f"http://img.youtube.com/vi/{video_id}/0.jpg"
        st.image(video_thumbnail, caption="Video Thumbnail", use_column_width=True)

if st.sidebar.button("📄 Get Detailed Notes", use_container_width=True):
    if not google_api_key:
        st.warning("Please enter your Google API Key before proceeding.")
    elif not youtube_link:
        st.warning("Please enter a valid YouTube video link.")
    else:
        with st.spinner("⏳ Extracting transcript and generating summary..."):
            transcript_text = extract_transcript_details(youtube_link)
            if transcript_text:
                summary = generate_gemini_content(transcript_text, summary_length, google_api_key)
                if summary:
                    st.success("✅ Summary generated successfully!")
                    st.subheader("📝 Detailed Notes:")
                    st.write(summary)

                    pdf_bytes = create_pdf(summary)
                    st.download_button(
                        label="📥 Download Summary as PDF",
                        data=pdf_bytes,
                        file_name="YouTube_Summary.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Failed to generate summary. Please try again.")
            else:
                st.error("No transcript could be extracted for this video.")
