# External imports
import streamlit as st
import tiktoken
from openai import OpenAI
import math
import ollama
from datetime import datetime

# Internal imports
from helper import api_key, secretmaker
from helper_chroma import ChromaDocStore

st.set_page_config(page_title="DocuChat", page_icon=":speech_balloon:", layout="wide")

# Initialize ChromaDocStore
doc_store = ChromaDocStore()

# Initialize the session key for the text

def main():
    # Current page sidebar
    st.sidebar.title("Chat Mode")
    st.sidebar.markdown("""
    Use this tab to get answers about your document.\n
    """)

    # Add file uploader to sidebar
    uploaded_file = st.sidebar.file_uploader(
        "Upload a document",
        type=["pdf", "docx"],
        help="Accepts PDF and Word documents.",
        key="chat_upload"
    )

    # Process uploaded file if present
    if uploaded_file:
        with st.sidebar.status("Processing document..."):
            parsed_text, tokens, model = parse_document(uploaded_file)
            if model:  # Document was processed successfully
                st.sidebar.success(f"Document '{uploaded_file.name}' processed and stored")
                # Set this as the active collection
                st.session_state.selected_collection = uploaded_file.name

    # Initialize collection selector state
    if "selected_collection" not in st.session_state:
        st.session_state.selected_collection = None

    # Get available collections
    collections = doc_store.list_collections()

    if collections:
        # Add collection selector below file uploader
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
            st.rerun()
    else:
        st.sidebar.info("No collections available. Upload a document to create one.")

    # Top level greeting
    st.title("DocuChat")
    st.markdown("Get answers to your questions about your document.")
    st.header(' ')  # Add some space


if __name__ == "__main__":
    main()

secretmaker()  # Create the st.secrets.json file if it doesn't exist
if not (st.secrets.api_keys.openai != "" or st.secrets.ollama.ollama_flag == 1):
    st.error("Please enter your OpenAI API key in the Settings tab or toggle Local Mode in the Settings tab.")
    st.stop()

# Maximum number of tokens to generate
gen_max_tokens = 500

doc_loaded = st.empty()


@st.cache_data(show_spinner=True, persist=True)
def parse_document(uploaded_file):
    text = ''
    tokens = 0
    if uploaded_file is None:  # Prevent error message when no file is uploaded
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
        encoding = tiktoken.encoding_for_model("gpt-4o")
        output = encoding.encode(text)
        tokens = len(encoding.encode(text))

        # Choose the right model based on the number of tokens. GPT-4o-mini only.
        if tokens == 0:
            model = None
        elif tokens <= 128000 - gen_max_tokens:
            model = "gpt-4o-mini"
        else:
            divider = math.ceil(tokens / 128000)
            st.error(f"Your document is too long! You need to choose a smaller document or divide yours in {divider} parts.")
            model = None
            st.stop()

        # Display the token count and model used inside a collapsible container
        with st.expander("Show details"):
            st.write(f"Number of tokens: {tokens}")
            st.write(f"Using model: {model}")

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


# Create the engine
if st.secrets.ollama.ollama_flag == 0:
    engine = OpenAI(api_key=api_key)
    engine_type = "openai"
    rag_model = "gpt-4o-mini"
else:
    engine = ollama.chat
    engine_type = "ollama"
    rag_model = st.secrets.ollama.default_model
# Request parameters
rag_model = "gpt-4o-mini" if st.secrets.ollama.ollama_flag == 0 else st.secrets.ollama.default_model

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
    # Get relevant chunks from the active collection
    collection_name = st.session_state.selected_collection

    if collection_name:
        relevant_chunks = get_relevant_chunks(prompt, collection_name)
        if relevant_chunks:
            context_prompt = (f"Here are the most relevant parts of the document for answering the question:\n\n{relevant_chunks}\n\n"
                            f"Please use this context to answer the question. If the context doesn't contain enough information, "
                            f"you can also refer to other parts of the document that you remember.")
        else:
            st.warning("Could not find relevant chunks. The answer might be less accurate.")
            context_prompt = "Please answer the question based on your knowledge of the document."

        # Create messages array with context as system message
        messages_to_send = [
            {"role": "system", "content": context_prompt}
        ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    else:
        st.error("Please select a collection first.")
        st.stop()

    # Create a chat message container for the assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            for response in engine(
                    model=rag_model,
                    messages=messages_to_send,
                    stream=True,
            ):
                if engine_type == "openai":
                    # Handle OpenAI streaming response
                    full_response += (response.choices[0].delta.content or "")
                else:
                    # Handle Ollama streaming response
                    if 'message' in response and 'content' in response['message']:
                        full_response += response['message']['content']

                # Update the message placeholder with the accumulated response
                message_placeholder.markdown(full_response + "▌")

            # Display final response without the typing indicator
            message_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"Error during streaming: {str(e)}")
            full_response = "Sorry, there was an error generating the response."
            message_placeholder.markdown(full_response)

    # Add the assistant message to the chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Add buttons to clear chat history and all data
def clear_chat_history():
    st.session_state.messages = []
    st.rerun()

def clear_all():
    st.session_state.messages = []
    st.session_state.selected_collection = None
    st.session_state.collection_selector = "None"
    st.rerun()

if len(st.session_state.messages) > 0:
    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)
st.sidebar.button('Clear All', on_click=clear_all)


# ------------------- LICENSE -------------------
# Docuchat, a smart knowledge assistant for your documents.
# Copyright © 2025 alxc75
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
