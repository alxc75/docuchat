# External imports
import streamlit as st
import tiktoken
from openai import OpenAI, OpenAIError
import math
import json
from datetime import datetime

# Internal imports
from helper import api_key, jsonmaker, endpoint
from helper_chroma import ChromaDocStore

st.set_page_config(page_title="DocuChat", page_icon=":speech_balloon:", layout="wide")

# Initialize ChromaDocStore
doc_store = ChromaDocStore()

# Initialize the session key for the text. See the end of parse_document() for writing.
if "text" not in st.session_state:
    st.session_state["text"] = ""

def main():
    # Current page sidebar
    st.sidebar.title("Summary")
    st.sidebar.markdown("""
    Use this tab to get a quick summary of your uploaded document.\n
    """)

    # Initialize collection selector state
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
    title, modeToggle = st.columns(2)
    title.title("DocuChat")
    modeToggle.toggle("Advanced Mode", value=False, key="simple_mode", disabled=True, help="Coming soon!")
    st.markdown("""
    Welcome to DocuChat, your smart knowledge assistant.

    Upload a document and a summary will be generated below. Use the Chat tab to ask questions about the document.
    """)
    st.header(' ') # Add some space


if __name__ == "__main__":
    main()

jsonmaker() # Create the userinfo.json file if it doesn't exist
with open("userinfo.json", "r") as f:
    userinfo = json.load(f)
    if not (userinfo["api_key"] != "" and userinfo["endpoint"] == "https://api.openai.com/v1/") and \
            not (userinfo["install_flag"] == 1 and userinfo["endpoint"] == "http://localhost:8080/v1"):

        st.error("Please enter your OpenAI API key in the Settings tab or toggle Local Mode in the Settings tab.")
        # Dump the userinfo.json variables for debug:
        # st.write(userinfo)
        st.stop()


# Maximum number of tokens to generate
gen_max_tokens = 500

# Upload file
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx"], help="Accepts PDF and Word documents.")


@st.cache_data(show_spinner=True, persist=True)
def parse_document(uploaded_file):
    text = ''
    tokens = 0
    if uploaded_file is None: # Prevent error message when no file is uploaded
        return text, tokens, None
    else:
        name = uploaded_file.name
        # Check the extension and load the appropriate library
        if name.endswith(".pdf"):
            import PyPDF2
            pdfReader = PyPDF2.PdfReader(uploaded_file)
            for page in range(len(pdfReader.pages)):
                page_obj = pdfReader.pages[page]
                text += page_obj.extract_text()

        elif name.endswith(".docx"):
            import docx2txt
            text = docx2txt.process(uploaded_file)

        # Count the number of tokens in the document
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        output = encoding.encode(text)
        tokens = len(encoding.encode(text))

        # Choose the right model based on the number of tokens. GPT-3.5-Turbo only.
        if tokens == 0:
            model = None
        elif tokens <= 16385 - gen_max_tokens:
            model = "gpt-4o-mini"
        else:
            divider = math.ceil(tokens / 16385)
            st.error(f"Your document is too long! You need to choose a smaller document or divide yours in {divider} parts.")
            model = None
            st.stop()

        # Display the token count and model used inside a collapsible container
        with st.expander("Show details"):
            st.write(f"Number of tokens: {tokens}")
            st.write(f"Using model: {model}")

        # Save the text to the session state
        st.session_state["text"] = text

        # Store document in Chroma
        if text.strip():
            metadata = {
                "filename": name,
                "upload_date": datetime.utcnow().isoformat(),
                "token_count": tokens,
                "model": model
            }
            # Use sanitized filename as collection name and document ID
            doc_store.add_document(
                collection_name=name,  # Will be sanitized inside ChromaDocStore
                text=text,
                metadata=metadata,
                doc_id=name  # Will be sanitized when generating chunk IDs
            )

        return text, tokens, model


# Load document either from uploaded file or selected collection
text = ''
tokens = 0
model = None

if uploaded_file:
    # Use the function to parse the uploaded file
    text, tokens, model = parse_document(uploaded_file)
elif st.session_state.selected_collection:
    try:
        # Query the entire document from the selected collection
        results = doc_store.query_documents(
            collection_name=st.session_state.selected_collection,
            query="",  # Empty query to get all chunks
            n_results=10  # Get a reasonable number of chunks
        )
        if results and results["documents"]:
            text = "\n\n".join(results["documents"][0])
            # Get metadata from first chunk
            metadata = results["metadatas"][0][0]
            tokens = metadata.get("token_count", 0)
            model = metadata.get("model", "gpt-4o-mini")
    except Exception as e:
        st.error(f"Error loading collection: {e}")
        st.session_state.selected_collection = None

with open("userinfo.json", "r") as f:
    userinfo = json.load(f)
    if userinfo["install_flag"] == 1:
        endpoint = userinfo['endpoint'] # Use the local model if Local Mode is enabled


# Create the OpenAI request
client = OpenAI(api_key=api_key, base_url=endpoint)
sys_prompt = ("You are an assistant designed to give summaries of uploaded documents. Your answers should be decently long, "
          "in the form of bullet points. Make sure to include every point discussed in the document. Being verbose is "
          "highly preferable compared to missing ideas in the document. Do not deviate from this command. You are to provide an objective summary without tangential analyses. Here is the document to recap:")

@st.cache_data(show_spinner=True, persist=True)
def generate_completion(text):
    if text == '':
        print("No document detected. No completion will be generated.")
        return ""

    try:
        # Get relevant chunks from Chroma if available
        collection_name = None
        if uploaded_file:
            collection_name = uploaded_file.name
        elif st.session_state.selected_collection:
            collection_name = st.session_state.selected_collection

        if collection_name:
            try:
                results = doc_store.query_documents(
                    collection_name=collection_name,  # Will be sanitized in query_documents
                    query="Summarize the main points of this document",
                    n_results=5  # Get top 5 most relevant chunks
                )
                # Use retrieved chunks instead of full text if available
                if results and results["documents"]:
                    text = "\n\n".join(results["documents"][0])  # Join top chunks
            except Exception as e:
                st.error(f"Error querying collection: {e}")

        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            max_tokens=gen_max_tokens,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text}
            ]
        )
        st.markdown("## Summary")
        response_text = response.choices[0].message.content

        # Add session state to keep the output text if the user switches tabs
        if 'saved_text' in st.session_state:
            st.session_state.saved_text = response_text
        else:
            st.session_state.saved_text = response_text
        st.cache_data.clear()

        return response_text

    except OpenAIError as e:
        print(f"An error occurred: {e}")
        return None


response_text = generate_completion(text)


output_wrapper = st.empty() # Create a wrapper around the output to allow for clearing it
# Add session state to keep the output text
if 'saved_text' not in st.session_state:
    output_wrapper.markdown(response_text)
else:
    output_wrapper.markdown(st.session_state.saved_text)


def regenerate_summary():
    st.cache_data.clear()
    output_wrapper.empty()


def clear_summary():
    st.session_state.saved_text = ''
    st.session_state.selected_collection = None  # Clear selected collection
    st.session_state.collection_selector = "None"  # Reset dropdown to None
    # st.session_state.text = ''    # Not removing the parsed text for now since it is used by the Chat tab.
    # st.cache_data.clear()         # No observable effect
    output_wrapper.empty()
    st.toast("Summary cleared!", icon="🔥")
    st.rerun()  # Rerun to update UI


# regen, clear = st.columns(2)
if len(response_text) > 0:
    st.sidebar.button("Regenerate summary", on_click=regenerate_summary)
    if st.sidebar.button("Clear summary", on_click=clear_summary):
        st.stop()


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
