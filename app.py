import streamlit as st
import os
import base64
from huggingface_hub import InferenceClient
from gtts import gTTS
import io

# --- Page Config ---
st.set_page_config(page_title="AstraToonix AI", page_icon="🤖")

st.title("🤖 AstraToonix AI Bot")
st.caption("Auto-Reply with Voice! 🔊")

# --- Function for Auto-Play Audio ---
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
    
    # Token check
    env_token = os.getenv("HF_TOKEN")
    if env_token:
        hf_token = env_token
        st.success("System Token Loaded! ✅")
    else:
        hf_token = st.text_input("Hugging Face Token", type="password")

    # --- MODEL LIST ---
    model_id = st.selectbox(
        "Choose Model",
        [
            "Qwen/Qwen2.5-72B-Instruct",       # Best Choice
            "microsoft/Phi-3.5-mini-instruct", # Fast Backup
            "google/gemma-2-2b-it"             # Simple Backup
        ]
    )
    
    voice_lang = st.selectbox("Voice Language", ["en", "hi"], index=0)
    
    if st.button("Clear Chat"):
        st.session_state.messages = []

# --- Memory ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "audio" in message:
            st.audio(message["audio"], format='audio/mp3')

# --- Main Logic ---
if prompt := st.chat_input("Message type karein..."):
    
    if not hf_token:
        st.error("Token missing! Please add it in sidebar.")
        st.stop()

    # 1. User Message
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. AI Reply
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            client = InferenceClient(model=model_id, token=hf_token)
            
            system_instruction = {
                "role": "system", 
                "content": "You are a helpful AI assistant. Keep answers short and natural."
            }
            
            history_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            history_for_api = [system_instruction] + history_messages

            stream = client.chat_completion(messages=history_for_api, max_tokens=400, stream=True)
            
            # --- FIX IS HERE (Updated Loop) ---
            for chunk in stream:
                # Hum check kar rahe hain ki 'choices' khali to nahi hai
                if chunk.choices and len(chunk.choices) > 0:
                    new_content = chunk.choices[0].delta.content
                    if new_content:
                        full_response += new_content
                        message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)

            # 3. Auto-Play Logic
            audio_data = None
            if full_response.strip():
                try:
                    tts = gTTS(text=full_response, lang=voice_lang, slow=False)
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    audio_data = audio_fp.getvalue()
                    autoplay_audio(audio_data)
                    
                except Exception as e:
                    print(f"Audio Error: {e}")

            # 4. Save to Memory
            msg_obj = {"role": "assistant", "content": full_response}
            if audio_data:
                msg_obj["audio"] = audio_data
            
            st.session_state.messages.append(msg_obj)

        except Exception as e:
            st.error(f"Error: {e}")
            
