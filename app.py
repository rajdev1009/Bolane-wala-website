import streamlit as st
import os
import base64
from huggingface_hub import InferenceClient
from gtts import gTTS
import io
import difflib  # Matching ke liye

# --- IMPORT DATABASE ---
# Agar movies_db.py file nahi milti to error na aaye, isliye try-except
try:
    from movies_db import data as movie_database
except ImportError:
    movie_database = {}  # Empty agar file na ho

# --- CONFIGURATION ---
OWNER_NAME = "Rajdev"
LOCATION = "Lumding, Assam"
MAIN_CHANNEL_LINK = "https://t.me/+u4cmm3JmIrFlNzZl" 

# --- Page Config ---
st.set_page_config(page_title="AstraToonix", page_icon="🤖")

st.title("🤖 AstraToonix")
st.caption(f"Created by {OWNER_NAME}")

# --- Helper: Search Movie Function ---
def find_movie_link(user_query):
    # User ki query ko lowercase karein
    query_lower = user_query.lower()
    
    # 1. Direct check
    for movie_name, link in movie_database.items():
        if movie_name in query_lower:
            return movie_name, link
            
    # 2. Fuzzy match (Agar spelling thodi galat ho)
    # Sirf tab check karein agar database me kuch ho
    if movie_database:
        matches = difflib.get_close_matches(query_lower, movie_database.keys(), n=1, cutoff=0.6)
        if matches:
            found_name = matches[0]
            return found_name, movie_database[found_name]
            
    return None, None

# --- Audio Function ---
def autoplay_audio(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""
        <audio controls autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    env_token = os.getenv("HF_TOKEN")
    if env_token:
        hf_token = env_token
        st.success("System Token Loaded! ✅")
    else:
        hf_token = st.text_input("Hugging Face Token", type="password")

    model_id = st.selectbox("Choose Model", ["Qwen/Qwen2.5-72B-Instruct", "microsoft/Phi-3.5-mini-instruct"])
    voice_lang = st.selectbox("Voice Language", ["hi", "en"], index=0)
    if st.button("Clear Chat"):
        st.session_state.messages = []

# --- Chat Logic ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "audio" in message:
            st.audio(message["audio"], format='audio/mp3')

if prompt := st.chat_input("Message type karein..."):
    if not hf_token:
        st.error("Token missing!")
        st.stop()

    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # --- SMART CHECK: Database Search ---
        found_movie, found_link = find_movie_link(prompt)
        
        # System Prompt ko Dynamic banate hain
        if found_movie:
            # Agar movie mil gayi database mein
            system_prompt_text = f"""
            You are AstraToonix. The user asked for '{prompt}'.
            We FOUND the movie '{found_movie}' in our database.
            
            YOUR TASK:
            1. Tell the user "Haan, {found_movie} hamare paas available hai!"
            2. Provide this EXACT link: {found_link}
            3. Say "Click the link above to watch directly."
            4. Keep it short.
            """
        else:
            # Agar movie database mein nahi hai
            system_prompt_text = f"""
            You are AstraToonix created by {OWNER_NAME}.
            User message: '{prompt}'
            
            RULES:
            1. If user is asking for a movie/series, say: "Filhal ye specific link database me nahi hai, par aap hamare main channel par search kar sakte hain." and give this link: {MAIN_CHANNEL_LINK}
            2. If user asks general questions (Who are you?), answer as AstraToonix (Creator: {OWNER_NAME}, from {LOCATION}).
            3. FOR CODING: Write full detailed code.
            """

        try:
            client = InferenceClient(model=model_id, token=hf_token)
            history_for_api = [{"role": "system", "content": system_prompt_text}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if "audio" not in m]

            stream = client.chat_completion(messages=history_for_api, max_tokens=3000, stream=True)
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)

            # Audio Logic
            audio_data = None
            if full_response.strip() and len(full_response) < 1000:
                try:
                    tts = gTTS(text=full_response, lang=voice_lang, slow=False)
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    audio_data = audio_fp.getvalue()
                    autoplay_audio(audio_data)
                except: pass

            msg_obj = {"role": "assistant", "content": full_response}
            if audio_data: msg_obj["audio"] = audio_data
            st.session_state.messages.append(msg_obj)

        except Exception as e:
            st.error(f"Error: {e}")
            
