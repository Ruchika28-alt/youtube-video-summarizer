import re
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI
import requests

# --- Initialize OpenAI LLM ---
llm = OpenAI(api_key=st.secrets["openai_api_key"], temperature=0.3)

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def get_video_metadata(video_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet"
    response = requests.get(url).json()
    if response.get("items"):
        snippet = response["items"][0]["snippet"]
        return snippet["title"], snippet["description"]
    return None, None

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except:
        return None

def summarize_text(text):
    prompt = PromptTemplate(
        input_variables=["text"],
        template=(
            "Summarize the following YouTube video transcript in 3–5 bullet points, "
            "highlighting key topics and any timestamps if mentioned:\n\n{text}\n\nSummary:"
        ),
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(text=text)

def process_youtube_video(url, youtube_api_key):
    video_id = extract_video_id(url)
    if not video_id:
        return "Invalid YouTube URL.", None, None

    title, description = get_video_metadata(video_id, youtube_api_key)
    transcript = get_transcript(video_id)

    if not transcript:
        summary = summarize_text(description or "No transcript or description available.")
        return title, f"Summary (from description): {summary}", None

    summary = summarize_text(transcript)
    return title, summary, transcript

# --- Streamlit UI ---
st.title("🎥 YouTube Video Summarizer")
st.write("Paste a YouTube video link below to get its transcript and summary.")

url = st.text_input("Enter YouTube URL:")
if st.button("Summarize"):
    if url:
        title, summary, transcript = process_youtube_video(url, st.secrets["youtube_api_key"])
        if title:
            st.subheader(f"📌 Title: {title}")
            st.subheader("📝 Summary:")
            st.write(summary)
            if transcript:
                st.subheader("🗒️ Full Transcript:")
                st.text_area("Transcript", transcript, height=300)
            else:
                st.info("Transcript not available.")
        else:
            st.error("❌ Failed to process the video. Please check the URL or API keys.")
    else:
        st.warning("⚠️ Please enter a valid YouTube URL.")



