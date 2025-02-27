import streamlit as st
import tiktoken
import math
from datetime import datetime

st.sidebar.title("Collections")
st.sidebar.markdown("Use this tab to add, modify or delete your document collections.")
st.title("Collections")
st.divider()

with st.spinner("Loading Collections..."):
    from helper_chroma import ChromaDocStore
    doc_store = ChromaDocStore()
gen_max_tokens = 500


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


# Initialize collection selector state
if "selected_collection" not in st.session_state:
    st.session_state.selected_collection = None

collections = doc_store.list_collections()

if collections:
    # Add collection selector below file uploader
    st.markdown("### Available Collections")
    selected = st.selectbox(
        "Select a collection to load",
        ["None"] + collections,
        index=0,
        key="collection_selector",
        help="Switch between previously uploaded documents"
    )

    # Handle collection selection
    if selected != "None" and selected != st.session_state.selected_collection:
        st.session_state.selected_collection = selected
        st.success(f"Loaded collection: {selected}")
        st.rerun()
else:
    st.info("No collections available. Upload a document below to create one.")



# Add file uploader to sidebar
uploaded_file = st.file_uploader(
    "Upload a document",
    type=["pdf", "docx"],
    help="Accepts PDF and Word documents.",
    key="chat_upload",
    accept_multiple_files=True
)
# Process uploaded file if present
if uploaded_file:
    with st.status("Processing document..."):
        parsed_text, tokens, model = parse_document(uploaded_file)
        if model:  # Document was processed successfully
            st.success(f"Document '{uploaded_file.name}' processed and stored")
            # Set this as the active collection
            st.session_state.selected_collection = uploaded_file.name