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


# Initialize collection related state
if "selected_collection" not in st.session_state:
    st.session_state.selected_collection = None
if "show_rename_dialog" not in st.session_state:
    st.session_state.show_rename_dialog = False
if "show_delete_dialog" not in st.session_state:
    st.session_state.show_delete_dialog = False

@st.cache_data(show_spinner=True, persist=True)
def parse_document(uploaded_file, collection_name=None):
    """Parse a single document and add it to a collection.

    Args:
        uploaded_file: The uploaded file object
        collection_name: Optional collection name (if None, use filename)

    Returns:
        tuple: (text, tokens, model, metadata)
    """
    text = ''
    tokens = 0

    if uploaded_file is None:  # Prevent error message when no file is uploaded
        return text, tokens, None, None

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

    # Create metadata
    metadata = {
        "filename": name,
        "upload_date": datetime.utcnow().isoformat(),
        "token_count": tokens,
        "model": model
    }

    # Store document in Chroma if text is not empty and model is valid
    if text.strip() and model:
        # Use provided collection_name or sanitized filename
        coll_name = collection_name if collection_name else name

        doc_store.add_document(
            collection_name=coll_name,  # Will be sanitized inside ChromaDocStore
            text=text,
            metadata=metadata,
            doc_id=name  # Use filename as document ID
        )

    return text, tokens, model, metadata

def process_multiple_files(uploaded_files, collection_name):
    """Process multiple uploaded files into a single collection.

    Args:
        uploaded_files: List of uploaded files
        collection_name: Custom collection name

    Returns:
        dict: Processing results with counts and file information
    """
    if not collection_name:
        # Use first filename as collection name if not provided
        collection_name = uploaded_files[0].name

    results = {
        "success_count": 0,
        "failed_files": [],
        "processed_files": [],
        "collection_name": collection_name,
        "total_tokens": 0
    }

    # Process each file
    for file in uploaded_files:
        try:
            text, tokens, model, metadata = parse_document(file, collection_name)

            if model:  # Document was processed successfully
                results["success_count"] += 1
                results["total_tokens"] += tokens
                results["processed_files"].append({
                    "filename": file.name,
                    "tokens": tokens,
                    "model": model
                })
            else:
                results["failed_files"].append(file.name)
        except Exception as e:
            results["failed_files"].append(f"{file.name} (Error: {str(e)})")

    return results

collections = doc_store.list_collections()

# Main page layout
col1, col2 = st.columns([2, 1])

with col1:
    if collections:
        st.subheader("Available Collections")
        selected = st.selectbox(
            "Select a collection to manage",
            ["None"] + collections,
            index=0,
            key="collection_selector",
            help="Switch between previously uploaded document collections"
        )

        # Handle collection selection
        if selected != "None" and selected != st.session_state.selected_collection:
            st.session_state.selected_collection = selected
            st.success(f"Loaded collection: {selected}")
            st.rerun()
    else:
        st.info("No collections available. Upload documents below to create one.")

# Add custom collection name input
with col2:
    custom_collection_name = st.text_input(
        "Collection Name (optional)",
        placeholder="Enter a name for your collection",
        help="If not provided, the first filename will be used"
    )

# Add file uploader
uploaded_file = st.file_uploader(
    "Upload Documents",
    type=["pdf", "docx"],
    help="Accepts PDF and Word documents. Upload multiple files to add them to a single collection.",
    key="chat_upload",
    accept_multiple_files=True
)

# Process uploaded files if present
if uploaded_file:
    processing_results = None
    single_file_details = None

    with st.status("Processing document(s)...") as status:
        if isinstance(uploaded_file, list):  # Multiple files
            if len(uploaded_file) > 0:
                results = process_multiple_files(uploaded_file, custom_collection_name)
                if results["success_count"] > 0:
                    status.update(label=f"Processed {results['success_count']} documents successfully")
                    st.success(f"Added {results['success_count']} documents to collection '{results['collection_name']}'")

                    # Set this as the active collection
                    st.session_state.selected_collection = results["collection_name"]

                    # Store results for display outside of status
                    processing_results = results
                else:
                    st.error("No documents were processed successfully")
        else:  # Single file (backward compatibility)
            text, tokens, model, metadata = parse_document(uploaded_file, custom_collection_name)
            if model:  # Document was processed successfully
                coll_name = custom_collection_name if custom_collection_name else uploaded_file.name
                st.success(f"Document '{uploaded_file.name}' processed and stored in collection '{coll_name}'")

                # Store details for display outside of status
                single_file_details = (uploaded_file.name, tokens, model, coll_name)

                # Set this as the active collection
                st.session_state.selected_collection = coll_name

    # Display processing details outside of status element
    if processing_results:
        with st.expander("Processing Details"):
            st.write(f"Total tokens: {processing_results['total_tokens']}")
            st.write("Processed files:")
            for file in processing_results["processed_files"]:
                st.write(f"- {file['filename']}: {file['tokens']} tokens")

            if processing_results["failed_files"]:
                st.error("Failed files:")
                for file in processing_results["failed_files"]:
                    st.write(f"- {file}")

    elif single_file_details:
        with st.expander("Show details"):
            st.write(f"Number of tokens: {single_file_details[1]}")
            st.write(f"Using model: {single_file_details[2]}")

# Display collection details if one is selected
if st.session_state.selected_collection:
    st.divider()
    collection_name = st.session_state.selected_collection

    # Create header area with collection name and management buttons
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.subheader(f"Collection: {collection_name}")

    with col2:
        # Add rename collection button
        if st.button("Rename Collection"):
            st.session_state.show_rename_dialog = True
            st.session_state.show_delete_dialog = False

    with col3:
        # Add delete collection button
        if st.button("Delete Collection", type="secondary"):
            st.session_state.show_delete_dialog = True
            st.session_state.show_rename_dialog = False

    # Handle rename dialog
    if st.session_state.get("show_rename_dialog", False):
        with st.form("rename_collection_form"):
            new_name = st.text_input(
                "New Collection Name",
                value=collection_name
            )
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("Rename")
            with col2:
                cancel = st.form_submit_button("Cancel")

            if submit and new_name and new_name != collection_name:
                try:
                    new_name = doc_store.rename_collection(collection_name, new_name)
                    st.session_state.selected_collection = new_name
                    st.session_state.show_rename_dialog = False
                    st.success(f"Collection renamed to {new_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error renaming collection: {str(e)}")

            if cancel:
                st.session_state.show_rename_dialog = False
                st.rerun()

    # Handle delete dialog
    if st.session_state.get("show_delete_dialog", False):
        with st.form("delete_collection_form"):
            st.warning(f"Are you sure you want to delete collection '{collection_name}'?")
            st.write("This action cannot be undone. All documents in this collection will be permanently deleted.")

            col1, col2 = st.columns([1, 1])
            with col1:
                confirm = st.form_submit_button("Delete Collection", type="primary")
            with col2:
                cancel = st.form_submit_button("Cancel")

            if confirm:
                try:
                    doc_store.delete_collection(collection_name)
                    st.session_state.selected_collection = None
                    st.session_state.show_delete_dialog = False
                    st.success(f"Collection '{collection_name}' has been deleted")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting collection: {str(e)}")

            if cancel:
                st.session_state.show_delete_dialog = False
                st.rerun()

    # Get collection info
    collection_info = doc_store.get_collection_info(collection_name)

    # Display collection metadata
    with st.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("Created", collection_info.get('created_at', 'Unknown')[:10] if 'created_at' in collection_info else 'Unknown')
        col2.metric("Documents", collection_info.get('document_count', 0))
        col3.metric("Chunks", collection_info.get('chunk_count', 0))

    # Display documents in the collection
    st.subheader("Documents in Collection")
    documents = doc_store.list_documents(collection_name)

    if not documents:
        st.info("No documents found in this collection")
    else:
        for doc in documents:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{doc.get('filename', 'Unknown')}**")
                with col2:
                    st.write(f"Uploaded: {doc.get('upload_date', 'Unknown')[:10]}")
                with col3:
                    if st.button("Delete", key=f"delete_{doc.get('id')}"):
                        if doc_store.delete_document(collection_name, doc.get('id')):
                            st.success(f"Document '{doc.get('filename')}' deleted")
                            st.rerun()
                        else:
                            st.error("Failed to delete document")

                st.write(f"Tokens: {doc.get('token_count', 0)} | Chunks: {doc.get('chunk_count', 0)}")
                st.divider()

    # Add "Upload to This Collection" option
    st.subheader("Add Documents to Collection")

    upload_to_current = st.file_uploader(
        f"Upload additional documents to '{collection_name}'",
        type=["pdf", "docx"],
        help="Adds documents to the currently selected collection",
        key="additional_upload",
        accept_multiple_files=True
    )

    if upload_to_current:
        with st.status("Adding documents to collection...") as status:
            results = process_multiple_files(
                upload_to_current,
                collection_name
            )

            if results["success_count"] > 0:
                status.update(label=f"Added {results['success_count']} documents to collection")
                st.success(f"Added {results['success_count']} documents to '{collection_name}'")
                st.rerun()
            else:
                st.error("No documents were added successfully")