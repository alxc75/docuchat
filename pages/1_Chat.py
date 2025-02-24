import streamlit as st
from openai import OpenAI
from helper import api_key
from main import parse_document, doc_store
import json
from datetime import datetime


# Initialize the session key for the text. See the end of parse_document() for writing.
if "text" not in st.session_state:
    st.session_state["text"] = ""
else:
    text = st.session_state["text"]


def main():
    # Current page sidebar
    st.sidebar.title("Chat Mode")
    st.sidebar.markdown("""
    Use this tab to get answers about your document.\n
    """)

    # Initialize collection selector state if not already done in main.py
    if "selected_collection" not in st.session_state:
        st.session_state.selected_collection = None

    # Get available collections
    collections = doc_store.list_collections()

    if collections:
        # Add collection selector
        st.sidebar.markdown("### Available Collections")
        selected = st.sidebar.selectbox(
            "Select a collection to load",
            ["None"] + collections,
            index=0,
            key="collection_selector",
            help="Switch between previously uploaded documents"
        )

        # Handle collection selection
        if selected != "None" and selected != st.session_state.selected_collection:
            st.session_state.selected_collection = selected
            st.sidebar.success(f"Loaded collection: {selected}")
            # Clear the file uploader state
            st.session_state["chat_upload"] = None
            # Force a rerun to update the UI
            st.rerun()
    else:
        st.sidebar.info("No collections available. Upload a document to create one.")

    # Top level greeting
    st.title("Chat Mode")
    st.markdown("Get answers to your questions about your document.")
    st.header(' ') # Add some space


if __name__ == "__main__":
    main()

doc_loaded = st.empty()
if len(st.session_state["text"]) > 0:
    doc_loaded.info("Using document loaded in memory. You can also upload a new document below.")

# Upload file
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx"], help="Accepts PDF and Word documents.", key="chat_upload")
parsed_text, tokens, model = parse_document(uploaded_file)
if uploaded_file is not None:
    st.session_state["text"] = parsed_text
    text = parsed_text
    doc_loaded.info("Loading complete!")
else:
    text = st.session_state["text"]

# Request parameters
gen_max_tokens = 500
engine = "gpt-4o-mini"
with open("userinfo.json", "r") as f:
    userinfo = json.load(f)
    if userinfo["install_flag"] == 1:
        endpoint = userinfo['endpoint'] # Use the local model if Local Mode is enabled

# Create the OpenAI request
client = OpenAI(api_key=api_key, base_url=endpoint)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept user input
if prompt := st.chat_input("What is your question?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

# Initialize the full response variable
full_response = ""

# Get relevant document chunks based on the user's question
def get_relevant_chunks(question: str, collection_name: str) -> str:
    try:
        results = doc_store.query_documents(
            collection_name=collection_name,  # Will be sanitized in ChromaDocStore
            query=question,
            n_results=3  # Get top 3 most relevant chunks
        )
        if results and results["documents"]:
            return "\n\n".join(results["documents"][0])  # Join top chunks
        return None
    except Exception as e:
        print(f"Error retrieving chunks: {e}")
        return None

# Send the request to OpenAI
if st.session_state.messages:  # Check if 'messages' is not empty
    messages_to_send = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    # Get relevant chunks either from uploaded file or selected collection
    collection_name = None
    if uploaded_file:
        collection_name = uploaded_file.name
    elif st.session_state.selected_collection:
        collection_name = st.session_state.selected_collection

    if collection_name:
        relevant_chunks = get_relevant_chunks(prompt, collection_name)
        if relevant_chunks:
            context_prompt = (f"Here are the most relevant parts of the document for answering the question:\n\n{relevant_chunks}\n\n"
                            f"Please use this context to answer the question. If the context doesn't contain enough information, "
                            f"you can also refer to other parts of the document that you remember.")
        else:
            context_prompt = f"Here is the full document:\n\n{text}\n\nPlease answer the question based on this document."
    else:
        st.error("Please upload a document or select a collection first.")
        st.stop()

        # Insert context as system message
        messages_to_send.insert(0, {"role": "system", "content": context_prompt})

    # Create a chat message container for the assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        for response in client.chat.completions.create(
                model=engine,
                messages=messages_to_send,
                stream=True,
                max_tokens=gen_max_tokens,
        ):
            full_response += (response.choices[0].delta.content or "")  # Handle empty or incoming response
            message_placeholder.markdown(full_response + "▌")  # Add a pipe to the end of the message to indicate typing since we're streaming
        message_placeholder.markdown(full_response)

    # Add the assistant message to the chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})


# Add a button to clear the chat history
def clear_chat_history():
    st.session_state.messages = []
    st.rerun()

def clear_all():
    st.session_state.messages = []
    st.session_state["text"] = ""
    st.session_state.selected_collection = None
    st.session_state.collection_selector = "None"
    if "text" in st.session_state:
        del st.session_state["text"]
    st.rerun()

if len(st.session_state.messages) > 0:
    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)
st.sidebar.button('Clear All', on_click=clear_all)


# ------------------- LICENSE -------------------
# Docuchat, a smart knowledge assistant for your documents.
# Copyright © 2024 xTellarin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see https://www.gnu.org/licenses/.
