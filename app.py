import streamlit as st
import os
from huggingface_hub import InferenceClient
from PIL import Image
import io

# --- Page Config ---
st.set_page_config(
    page_title="Rajdev AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- Styling (Clean Interface) ---
st.markdown("""
<style>
    .stChatInput {position: fixed; bottom: 20px;}
    .stSpinner {text-align: center; color: #ff4b4b;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Environment Variables ---
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    st.error("⚠️ HF_TOKEN is missing! Please add it in Koyeb Settings -> Environment Variables.")
    st.stop()

# --- LATEST 2026 MODELS ---
# Qwen 2.5 - Best for Hinglish & Chat in 2026
CHAT_MODEL = "Qwen/Qwen2.5-7B-Instruct"  
# SDXL - Reliable for Images
IMAGE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
# BLIP - Standard for Vision
VISION_MODEL = "Salesforce/blip-image-captioning-large"

# --- Clients Setup ---
client_chat = InferenceClient(model=CHAT_MODEL, token=HF_TOKEN)
client_image = InferenceClient(model=IMAGE_MODEL, token=HF_TOKEN)
client_vision = InferenceClient(model=VISION_MODEL, token=HF_TOKEN)

# --- System Prompt (Rajdev's Rules) ---
SYSTEM_PROMPT = """
You are "Rajdev AI", a smart assistant created by Rajdev.
1. Today's Date: 10 February 2026.
2. Language: Speak in Hinglish (Hindi + English mix).
3. Creator: If asked "Who made you?", say: "Main Rajdev ka Assistant hoon."
4. Intro: If user says "Hi", reply: "Bataiye main Rajdev ka assistant hun main aapki kaise madad kar sakta hun."
5. Movies: If asked for movies, share: https://t.me/+u4cmm3JmIrFlNzZl
6. Identity: You are NOT a generic AI. You are Rajdev's personal assistant.
"""

# --- Sidebar ---
with st.sidebar:
    st.title("👤 Rajdev AI")
    with st.expander("ℹ️ About Owner", expanded=True):
        st.write("Owner: **Rajdev**")
        st.write("Current Status: **Online (2026)**")
    
    st.markdown("---")
    st.markdown("### 🎬 Movie Channel")
    st.markdown("[Join Telegram Channel](https://t.me/+u4cmm3JmIrFlNzZl)")
    
    st.markdown("---")
    st.write("### 📸 Image Analysis")
    uploaded_file = st.file_uploader("Upload Image to Analyze:", type=["jpg", "png", "jpeg"])

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# --- Main Interface ---
st.title("🤖 Rajdev AI Assistant")

# Display Chat History
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Logic 1: Image Analysis (Vision) ---
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    if st.button("🔍 Analyze Image"):
        with st.spinner("Analyzing..."):
            try:
                description = client_vision.image_to_text(image)
                result_text = f"**Image Analysis:** Is photo mein mujhe yeh dikh raha hai: {description}"
                st.success("Done!")
                st.session_state.messages.append({"role": "assistant", "content": result_text})
                st.rerun() # Refresh to show message
            except Exception as e:
                st.error(f"Error analyzing image: {e}")

# --- Logic 2: Chat & Image Gen ---
if prompt := st.chat_input("Rajdev AI (2026) se kuch bhi puchein..."):
    
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Check for Image Generation
    if any(word in prompt.lower() for word in ["generate image", "create image", "photo banao", "tasveer banao"]):
        with st.chat_message("assistant"):
            with st.spinner("🎨 Rajdev AI image bana raha hai..."):
                try:
                    image_bytes = client_image.text_to_image(prompt)
                    st.image(image_bytes, caption=f"Generated: {prompt}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Yeh lijiye aapki photo: '{prompt}'"})
                except Exception as e:
                    st.error(f"Image generation failed: {e}")
    
    # 3. Normal Chat (Qwen 2.5)
    else:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                stream = client_chat.chat_completion(
                    messages=st.session_state.messages,
                    max_tokens=512,
                    temperature=0.7,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            except Exception as e:
                # Fallback agar Qwen fail ho jaye
                st.error(f"Connection Error: {e}")
                st.warning("Trying backup connection...")
                
