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

# --- CSS Styling ---
st.markdown("""
<style>
    .stChatInput {position: fixed; bottom: 20px;}
    .stSpinner {text-align: center;}
</style>
""", unsafe_allow_html=True)

# --- Environment Variables ---
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    st.error("⚠️ HF_TOKEN is missing! Add it in Koyeb Variables.")
    st.stop()

# --- Models ---
# 1. Chat Model (Fast)
CHAT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
# 2. Image Generation Model
IMAGE_GEN_MODEL = "stabilityai/stable-diffusion-xl-base-1.0" 
# 3. Vision Model (Image Analysis)
VISION_MODEL = "Salesforce/blip-image-captioning-large"

client = InferenceClient(token=HF_TOKEN)

# --- System Prompt (Rajdev Rules) ---
SYSTEM_PROMPT = """
You are "Rajdev AI", a smart assistant created by Rajdev.
1. Always answer in Hinglish (Hindi + English mix).
2. If asked "Who made you?", say: "Main Rajdev ka Assistant hoon."
3. If user says "Hi/Hello", reply: "Bataiye main Rajdev ka assistant hun main aapki kaise madad kar sakta hun."
4. If asked for movies, give link: https://t.me/+u4cmm3JmIrFlNzZl
5. Be fast, helpful, and never mention you are a generic AI.
"""

# --- Sidebar: Image Upload & Profile ---
with st.sidebar:
    st.title("👤 Rajdev AI")
    st.info("Owner: Rajdev")
    st.markdown("[🎬 Movie Channel](https://t.me/+u4cmm3JmIrFlNzZl)")
    
    st.markdown("---")
    st.write("### 📸 Image Analysis")
    uploaded_file = st.file_uploader("Upload an image to analyze:", type=["jpg", "png", "jpeg"])

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- Main Chat UI ---
st.title("🤖 Rajdev AI Assistant")

# Display History
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            # Check if content is an image path or text
            if isinstance(message["content"], str) and message["content"].startswith("http"): 
                 # This is a placeholder for generated image URL if we had one, 
                 # but for now we display bytes directly in generation step.
                 st.markdown(message["content"])
            else:
                st.markdown(message["content"])

# --- Logic: Image Analysis (Vision) ---
if uploaded_file:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    # Analyze button
    if st.button("🔍 Analyze this Image"):
        with st.spinner("Analyzing image..."):
            try:
                # Use HF API for Image to Text
                res = client.image_to_text(image, model=VISION_MODEL)
                description = res  # Usually returns a string description
                
                response_text = f"**Image Analysis:** Is photo mein mujhe yeh dikh raha hai: {description}"
                st.success(response_text)
                
                # Add to chat history
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Error analyzing image: {e}")

# --- Logic: Chat & Image Generation ---
if prompt := st.chat_input("Rajdev AI se kuch bhi puchein..."):
    
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Check for Image Generation Command
    if "generate image" in prompt.lower() or "create image" in prompt.lower() or "photo banao" in prompt.lower():
        with st.chat_message("assistant"):
            with st.spinner("🎨 Rajdev AI image bana raha hai..."):
                try:
                    # Generate Image
                    image_bytes = client.text_to_image(prompt, model=IMAGE_GEN_MODEL)
                    st.image(image_bytes, caption=f"Generated: {prompt}")
                    
                    # Note: We can't easily save bytes to history in this simple setup without a database,
                    # so we just show it.
                    st.session_state.messages.append({"role": "assistant", "content": f"Maine '{prompt}' ki photo bana di hai! 👆"})
                except Exception as e:
                    st.error(f"Image generation failed: {e}")
    
    else:
        # Normal Text Chat (Streaming)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                stream = client.chat_completion(
                    messages=st.session_state.messages,
                    max_tokens=500,
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
        
