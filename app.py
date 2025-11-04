import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from youtube_transcript_api import YouTubeTranscriptApi
import re

# --- App title ---
st.title("🎥 YouTube Video Summarizer")

# --- API keys from Streamlit secrets ---
openai_api_key = st.secrets["openai_api_key"]
youtube_api_key = st.secrets["youtube_api_key"]

# --- Get YouTube video URL ---
url = st.text_input("Enter YouTube video URL")

# --- Extract transcript ---
def get_transcript(video_url):
    video_id = re.findall(r"v=([a-zA-Z0-9_-]{11})", video_url)
    if not video_id:
        return None
    transcript = YouTubeTranscriptApi.get_transcript(video_id[0])
    return " ".join([t["text"] for t in transcript])

# --- Load transcript ---
if url:
    with st.spinner("Fetching transcript..."):
        transcript = get_transcript(url)

    if transcript:
        st.success("Transcript fetched successfully!")

        # --- Summarization prompt ---
        template = """Summarize the following YouTube video transcript in concise bullet points:\n\n{transcript}"""
        prompt = PromptTemplate(input_variables=["transcript"], template=template)

        # --- Initialize model ---
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, api_key=openai_api_key)
        chain = LLMChain(llm=llm, prompt=prompt)

        # --- Generate summary ---
        with st.spinner("Generating summary..."):
            summary = chain.run(transcript)

        st.subheader("📝 Summary")
        st.write(summary)
    else:
        st.error("Could not fetch transcript. Check the video URL.")
