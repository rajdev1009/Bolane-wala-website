import streamlit as st
import os
from huggingface_hub import InferenceClient
from PIL import Image
import io

# --- Page Config (Must be first) ---
st.set_page_config(
    page_title="Rajdev AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- Styling ---
st.markdown("""
<style>
    .stChatInput {position: fixed; bottom: 20px;}
    .stSpinner {text-align: center; color: #ff4b4b;}
    /* Hide Streamlit footer */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Environment Variables ---
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    st.error("⚠️ HF_TOKEN is missing! Please add it in Koyeb Settings -> Environment Variables.")
    st.stop()

# --- DEFINING MODELS EXPLICITLY (To fix Connection Error) ---
CHAT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
IMAGE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
VISION_MODEL = "Salesforce/blip-image-captioning-large"

# --- Creating Specific Clients ---
# Chat Client
client_chat = InferenceClient(model=CHAT_MODEL, token=HF_TOKEN)
# Image Generation Client
client_image = InferenceClient(model=IMAGE_MODEL, token=HF_TOKEN)
# Vision (Image Analysis) Client
client_vision = InferenceClient(model=VISION_MODEL, token=HF_TOKEN)

# --- System Prompt ---
SYSTEM_PROMPT = """
You are "Rajdev AI", a smart assistant created by Rajdev.
1. Language: Hinglish (Hindi + English mix).
2. Creator: If asked "Who made you?", say: "Main Rajdev ka Assistant hoon."
3. Intro: If user says "Hi", reply: "Bataiye main Rajdev ka assistant hun main aapki kaise madad kar sakta hun."
4. Movies: For movies, share link: https://t.me/+u4cmm3JmIrFlNzZl
5. Identity: Never say you are a generic AI. You are Rajdev's assistant.
"""

# --- Sidebar ---
with st.sidebar:
    st.title("👤 Rajdev AI")
    with st.expander("ℹ️ About Owner", expanded=True):
        st.write("Owner: **Rajdev**")
        st.write("Developer & Automation Expert")
    
    st.markdown("---")
    st.markdown("[🎬 Join Movie Channel](https://t.me/+u4cmm3JmIrFlNzZl)")
    
    st.markdown("---")
    st.write("### 📸 Image Analysis")
    uploaded_file = st.file_uploader("Upload Image to Analyze:", type=["jpg", "png", "jpeg"])

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- Main Interface ---
st.title("🤖 Rajdev AI Assistant")

# Show History
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            # Check if content is text or image caption
            st.markdown(message["content"])

# --- Logic 1: Analyze Uploaded Image ---
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    if st.button("🔍 Analyze Image"):
        with st.spinner("Analyzing..."):
            try:
                # Using explicit vision client
                description = client_vision.image_to_text(image)
                result_text = f"**Image Analysis:** Is photo mein mujhe yeh dikh raha hai: {description}"
                st.success(result_text)
                st.session_state.messages.append({"role": "assistant", "content": result_text})
            except Exception as e:
                st.error(f"Error analyzing image: {e}")

# --- Logic 2: Chat & Image Gen ---
if prompt := st.chat_input("Rajdev AI se kuch bhi puchein..."):
    
    # 1. User Message Display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Check if user wants to generate image
    if any(word in prompt.lower() for word in ["generate image", "create image", "photo banao", "tasveer banao"]):
        with st.chat_message("assistant"):
            with st.spinner("🎨 Rajdev AI image bana raha hai..."):
                try:
                    # Using explicit image client
                    image_bytes = client_image.text_to_image(prompt)
                    st.image(image_bytes, caption=f"Generated: {prompt}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Yeh lijiye aapki photo: '{prompt}'"})
                except Exception as e:
                    st.error(f"Image generation failed: {e}")
    
    # 3. Normal Chat
    else:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Using explicit chat client
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
                st.error(f"Connection Error: {e}")
                
