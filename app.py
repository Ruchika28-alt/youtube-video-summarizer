import re
import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi

# ✅ Updated imports for latest LangChain (0.3+)
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from langchain.chains import LLMChain

# Initialize LLM with your secret key
llm = OpenAI(api_key=st.secrets["openai_api_key"], temperature=0.3)

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|$)", url)
    if not match:
        match = re.search(r"youtu\.be\/([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

def get_video_metadata(video_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet"
    resp = requests.get(url)
    if resp.status_code != 200:
        return None, None
    data = resp.json()
    if data.get("items"):
        snippet = data["items"][0]["snippet"]
        return snippet.get("title"), snippet.get("description")
    return None, None

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except Exception:
        return None

def summarize_text(text):
    prompt = PromptTemplate(
        input_variables=["text"],
        template=(
            "Summarize the following YouTube video transcript in 3-5 bullet points, "
            "highlighting key topics and any important timestamps if mentioned:\n\n{text}\n\nSummary:"
        )
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(text=text)

def process_youtube_video(url, youtube_api_key):
    video_id = extract_video_id(url)
    if not video_id:
        return None, "Invalid YouTube URL.", None

    title, description = get_video_metadata(video_id, youtube_api_key)
    transcript = get_transcript(video_id)

    if not transcript:
        summary = summarize_text(description or "No description available.")
        return title, f"Summary (from description, no transcript available): {summary}", None

    summary = summarize_text(transcript)
    return title, summary, transcript

st.title("🎥 YouTube Video Summarizer")
st.write("Paste a YouTube link to get a summary and transcript.")

url = st.text_input("YouTube URL:")
if st.button("Summarize"):
    if not url:
        st.warning("Please enter a URL.")
    else:
        title, summary, transcript = process_youtube_video(url, st.secrets["youtube_api_key"])
        if title:
            st.subheader(f"Title: {title}")
            st.subheader("Summary:")
            st.write(summary)
            if transcript:
                st.subheader("Full Transcript:")
                st.text_area("Transcript", transcript, height=300)
            else:
                st.write("Transcript not available.")
        else:
            st.error(summary)

