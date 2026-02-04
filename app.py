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
    """
    Ye function audio ko turant play kar dega bina button dabaye.
    """
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

    # Model Selection
    model_id = st.selectbox(
        "Choose Model",
        ["HuggingFaceH4/zephyr-7b-beta", "mistralai/Mistral-7B-Instruct-v0.2"]
    )
    
    # Language
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
        # History me hum player dikhayenge, par auto-play nahi (sirf naye message pe auto-play hoga)
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
            
            # System Instruction
            system_instruction = {
                "role": "system", 
                "content": "You are a helpful AI assistant. Keep answers short and natural."
            }
            
            # Context preparation
            history_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            history_for_api = [system_instruction] + history_messages

            # Generate Text
            stream = client.chat_completion(messages=history_for_api, max_tokens=400, stream=True)
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
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
                    
                    # Yaha humne custom function call kiya jo AUTOMATIC play karega
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
