import streamlit as st
from PIL import Image
import io

# --- Custom Modules Import ---
# Humne jo files banayi hain unko yahan import kar rahe hain
import style
import bot_logic
import movies_db

# --- Page Config ---
st.set_page_config(
    page_title="Rajdev AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Check Token (From bot_logic)
bot_logic.check_token()

# 2. Apply Design (From style)
style.apply_custom_style()

# --- Sidebar ---
with st.sidebar:
    st.title("👤 Rajdev AI")
    with st.expander("ℹ️ About Owner", expanded=True):
        st.write("Owner: **Rajdev**")
        st.write("Status: **Online (2026)**")
    
    st.markdown("---")
    st.markdown("### 🎬 Movie Channel")
    st.markdown("[Join Telegram Channel](https://t.me/+u4cmm3JmIrFlNzZl)")
    
    st.markdown("---")
    st.write("### 📸 Image Analysis")
    uploaded_file = st.file_uploader("Photo Upload Karein:", type=["jpg", "png", "jpeg"])
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- Session State ---
if "messages" not in st.session_state:
    # System prompt bot_logic se lekar aayenge
    st.session_state.messages = [
        {"role": "system", "content": bot_logic.get_system_prompt()}
    ]

# --- Main Interface ---
st.title("🤖 Rajdev AI Assistant")

# Display Chat History
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            # Agar message image hai
            if isinstance(message["content"], tuple) and message["content"][0] == "image":
                st.image(message["content"][1], caption=message["content"][2])
            else:
                st.markdown(message["content"])

# --- Logic 1: Vision (Image Analysis) ---
if uploaded_file:
    image = Image.open(uploaded_file)
    st.sidebar.image(image, caption="Preview", use_column_width=True)
    
    if st.sidebar.button("🔍 Analyze Image"):
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    description = bot_logic.client_vision.image_to_text(image)
                    result_text = f"**👁️ Image Analysis:** Is photo mein mujhe yeh dikh raha hai: {description}"
                    st.markdown(result_text)
                    st.session_state.messages.append({"role": "assistant", "content": result_text})
                except Exception as e:
                    st.error(f"Error: {e}")

# --- Logic 2: Chat & Gen AI ---
if prompt := st.chat_input("Rajdev AI se kuch bhi puchein..."):
    
    # User Msg
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # A. Check for Image Generation Keywords
    img_triggers = ["generate image", "create image", "photo banao", "tasveer banao", "draw"]
    
    if any(word in prompt.lower() for word in img_triggers):
        with st.chat_message("assistant"):
            with st.spinner("🎨 Rajdev AI image bana raha hai..."):
                try:
                    image_bytes = bot_logic.client_image.text_to_image(prompt)
                    st.image(image_bytes, caption=f"Generated: {prompt}")
                    
                    # Add Download Button Logic
                    buf = io.BytesIO()
                    image_bytes.save(buf, format="PNG")
                    st.download_button(label="⬇️ Download", data=buf.getvalue(), file_name="rajdev_gen.png", mime="image/png")
                    
                    # Save to history
                    st.session_state.messages.append({"role": "assistant", "content": ("image", image_bytes, prompt)})
                except Exception as e:
                    st.error(f"Image generation failed: {e}")

    # B. Check for Movies (from movies_db)
    elif "movie" in prompt.lower() or "film" in prompt.lower():
        # Simple check: agar user ne specific movie maangi hai
        found_movie = False
        for movie_name, link in movies_db.movie_data.items():
            if movie_name in prompt.lower():
                response = f"🎬 **{movie_name.title()}** movie yahan available hai: [Download Link]({link})"
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                found_movie = True
                break
        
        if not found_movie:
            # Normal chat fallback if movie not found locally
            with st.chat_message("assistant"):
                msg_placeholder = st.empty()
                full_response = ""
                try:
                    stream = bot_logic.client_chat.chat_completion(
                        messages=st.session_state.messages, max_tokens=512, temperature=0.7, stream=True
                    )
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            msg_placeholder.markdown(full_response + "▌")
                    msg_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"Error: {e}")

    # C. Normal Chat
    else:
        with st.chat_message("assistant"):
            msg_placeholder = st.empty()
            full_response = ""
            try:
                # Send history without images to LLM
                text_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if isinstance(m["content"], str)]
                
                stream = bot_logic.client_chat.chat_completion(
                    messages=text_messages, max_tokens=1024, temperature=0.7, stream=True
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        msg_placeholder.markdown(full_response + "▌")
                
                msg_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Connection Error: {e}")
                
