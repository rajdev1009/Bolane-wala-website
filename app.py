import streamlit as st
import os
import base64
import asyncio
import math
import io
from huggingface_hub import InferenceClient
from telethon import TelegramClient
from dotenv import load_dotenv

# --- 1. SETUP & SECURITY ---
load_dotenv()

# Environment Variables Check
try:
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    # Telegram Keys
    tg_api_id = os.getenv("TELEGRAM_API_ID")
    API_ID = int(tg_api_id) if tg_api_id else None
    
    API_HASH = os.getenv("TELEGRAM_API_HASH")
    
    # Channel ID
    ch_id = os.getenv("CHANNEL_ID")
    CHANNEL_ID = int(ch_id) if ch_id else None
    
    # Bot Token
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")

    # Identity
    OWNER_NAME = os.getenv("OWNER_NAME", "Rajdev") 
    LOCATION = "Lumding, Assam"
    
except Exception:
    pass 

# --- Page Config ---
st.set_page_config(page_title="AstraToonix", page_icon="🤖")
st.title("🤖 AstraToonix AI")
st.caption(f"Assistant of {OWNER_NAME} | {LOCATION}")

# --- 2. HELPER FUNCTIONS ---
def convert_size(size_bytes):
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def autoplay_audio(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""
        <audio controls autoplay>
        <source src="data:audio/wav;base64,{b64}" type="audio/wav">
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)

# --- 3. SEARCH ENGINE ---
async def search_telegram_channel(query):
    # Greeting detection logic handled in chat loop to save API calls
    if query.lower().strip() in ['hi', 'hello', 'hey', 'namaste', 'kaise ho']:
        return None

    if not API_ID or not API_HASH or not CHANNEL_ID or not TG_BOT_TOKEN:
        return "CONFIG_ERROR"

    try:
        client = TelegramClient('bot_session_hf_voice', API_ID, API_HASH)
        await client.start(bot_token=TG_BOT_TOKEN)
        
        result_data = None
        async for message in client.iter_messages(CHANNEL_ID, search=query, limit=1):
            clean_id = str(CHANNEL_ID).replace("-100", "")
            msg_link = f"https://t.me/c/{clean_id}/{message.id}"
            upload_date = message.date.strftime("%d %B %Y")
            caption = message.text[:200] + "..." if message.text else "No Description"
            
            file_size = "Unknown"
            file_ext = "Link"
            if message.file:
                file_size = convert_size(message.file.size)
                file_ext = message.file.ext if message.file.ext else ".mp4"
                
            result_data = {
                "found": True,
                "link": msg_link,
                "date": upload_date,
                "size": file_size,
                "format": file_ext,
                "caption": caption
            }
            break 
            
        await client.disconnect()
        return result_data
    except Exception:
        return None

def get_movie_data(query):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(search_telegram_channel(query))

# --- 4. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "audio" in message:
            st.audio(message["audio"], format='audio/wav')

if prompt := st.chat_input("Type a message..."):
    
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Search Telegram
        search_result = get_movie_data(prompt)
        
        # --- IDENTITY & PROMPTS ---
        system_prompt = f"""
        You are AstraToonix.
        IDENTITY: Created by '{OWNER_NAME}' (Rajdev) from '{LOCATION}'.
        
        GREETING RULE: If user says 'Hi'/'Hello'/'Namaste' -> Reply EXACTLY:
        "Namaste! Main {OWNER_NAME} ka assistant hoon. Bataiye main aapki kaise madad kar sakta hoon?"
        
        CONTEXT:
        """

        if search_result == "CONFIG_ERROR":
            system_prompt += "\nNote: Database Keys missing. Chat normally."
            
        elif search_result and search_result.get("found"):
            system_prompt += f"""
            User asked for '{prompt}'.
            FOUND IN CHANNEL:
            - Link: {search_result['link']}
            - Size: {search_result['size']}
            - Date: {search_result['date']}
            
            TASK: Inform user clearly with details and Link.
            """
        else:
            system_prompt += f"""
            User said: '{prompt}'.
            - If Greeting: Follow GREETING RULE.
            - If Code: Provide detailed code.
            - If Movie: Say "Sorry, currently not in database."
            - If Who are you: "{OWNER_NAME} from {LOCATION}".
            """

        try:
            if not HF_TOKEN:
                st.error("Hugging Face Token Missing!")
                st.stop()

            # 1. Text Generation (Chat)
            client = InferenceClient(token=HF_TOKEN)
            
            stream = client.chat_completion(
                model="Qwen/Qwen2.5-72B-Instruct",
                messages=[{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                max_tokens=3000, 
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # 2. Voice Generation (Hugging Face API - No gTTS)
            # Hum Hindi/English mix model use karenge: facebook/mms-tts-hin
            audio_data = None
            if len(full_response) < 600: # Sirf chhote messages ke liye
                try:
                    # Yahan hum direct HF Inference API use kar rahe hain
                    # 'facebook/mms-tts-hin' Hindi ke liye best free model hai HF par
                    audio_bytes = client.text_to_speech(full_response, model="facebook/mms-tts-hin")
                    
                    if audio_bytes:
                        autoplay_audio(audio_bytes)
                        audio_data = audio_bytes
                except Exception as e:
                    # Agar audio fail ho jaye to silent rahe, error na dikhaye
                    print(f"Audio Error: {e}")

            st.session_state.messages.append({"role": "assistant", "content": full_response, "audio": audio_data})

        except Exception as e:
            st.error(f"AI Error: {e}")
        
