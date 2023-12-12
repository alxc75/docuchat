import streamlit as st
from st_pages import Page, show_pages

# Create the navigation bar
# show_pages(
#     [
#         Page("Home.py", "Home", ":house:"),
#         Page("pages/Summarizer.py", "Summary", ":document:"),
#         Page("pages/2_Chat.py", "Chat", ":speech_balloon:"),
#         Page("pages/Settings.py", "Settings", ":gear:"),
#         Page("pages/3_FAQ.py", "Help & FAQ", ":question:"),
#         Page("pages/99_Local_Mode.py", "Local Mode", "💻")
#     ]
# )

# Current page sidebar
st.sidebar.title("Home")
st.sidebar.markdown("""
Welcome to DocuChat! Use this sidebar to move around the application.\n
""")

# Top level greeting
title, modeToggle = st.columns(2)
title.title("DocuChat")
modeToggle.toggle("Advanced Mode", value=False, key="simple_mode", disabled=True, help="Coming soon!")
st.markdown("""
Welcome to DocuChat, your smart knowledge assistant.

Upload a document and a summary will be generated below. Use the Chat tab to ask questions about the document.
""")
st.header(' ') # Add some space