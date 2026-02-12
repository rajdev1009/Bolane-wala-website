import os
import datetime
from huggingface_hub import InferenceClient
import streamlit as st

# --- Environment Check ---
HF_TOKEN = os.environ.get("HF_TOKEN")

# --- Clients Setup (Models) ---
# Agar token nahi hai to error handle karein
if HF_TOKEN:
    client_chat = InferenceClient(model="Qwen/Qwen2.5-7B-Instruct", token=HF_TOKEN)
    client_image = InferenceClient(model="stabilityai/stable-diffusion-xl-base-1.0", token=HF_TOKEN)
    client_vision = InferenceClient(model="Salesforce/blip-image-captioning-large", token=HF_TOKEN)
else:
    client_chat = None
    client_image = None
    client_vision = None

# --- System Prompt (Rules) ---
def get_system_prompt():
    current_time = datetime.datetime.now().strftime("%d %B %Y")
    
    return f"""
    You are "Rajdev AI", a smart assistant created by Rajdev.
    
    RULES:
    1. Today's Date: {current_time}.
    2. Language: Speak in Hinglish (Hindi + English mix).
    3. Creator: If asked "Who made you?", say: "Main Rajdev ka Assistant hoon."
    4. Identity: You are NOT a generic AI. You are Rajdev's personal assistant.
    5. Movies: If user asks for a specific movie, check if you can provide it, otherwise share the channel: https://t.me/+u4cmm3JmIrFlNzZl
    6. Tone: Be friendly, professional and helpful.
    """

# --- Helper Functions ---
def check_token():
    if not HF_TOKEN:
        st.error("⚠️ HF_TOKEN is missing! Koyeb Settings me Environment Variables check karein.")
        st.stop()
      
