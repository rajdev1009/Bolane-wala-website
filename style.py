import streamlit as st

def apply_custom_style():
    st.markdown("""
    <style>
        /* Chat Input Fixed at Bottom */
        .stChatInput {
            position: fixed;
            bottom: 20px;
            z-index: 1000;
            background-color: transparent;
        }
        
        /* Message Bubbles Styling */
        .stChatMessage {
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 5px;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }
        
        /* Hide Default Streamlit Elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Spinner Style */
        .stSpinner {
            text-align: center;
            color: #ff4b4b;
        }
        
        /* Sidebar Padding */
        section[data-testid="stSidebar"] .block-container {
            padding-top: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
  
