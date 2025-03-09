import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_unstructured import UnstructuredLoader
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Tuple
import re
import os
from sentence_transformers import SentenceTransformer
import pandas as pd
from datetime import datetime


st.sidebar.title("LangChain Chroma Manager")
st.sidebar.markdown("LangChain Chroma Manager")
st.title("LangChain Chroma Manager")


class ChromaDocStore:
    def __init__(self, persist_dir: str = "./langchain"):
        """Initialize the Chroma document store.

        Args:
            persist_dir: Directory for persistent storage
        """
        # Create persist directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)

        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                allow_reset=True,
                is_persistent=True
            )
        )

        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def _sanitize_collection_name(self, name: str) -> str:
        """Sanitize collection name to meet Chroma requirements.

        Args:
            name: Original collection name

        Returns:
            str: Sanitized collection name
        """
        # Remove file extension
        name = os.path.splitext(name)[0]

        # Replace special characters and spaces with underscores
        name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)

        # Ensure it starts and ends with alphanumeric character
        name = re.sub(r'^[^a-zA-Z0-9]+', '', name)
        name = re.sub(r'[^a-zA-Z0-9]+$', '', name)

        # Ensure length is between 3 and 63 characters
        if len(name) < 3:
            name = name + "_doc"
        if len(name) > 63:
            name = name[:63]
            # Ensure it ends with alphanumeric
            name = re.sub(r'[^a-zA-Z0-9]+$', '', name)

        return name

    def list_collections(self) -> List[str]:
        """List all collections.

        Returns:
            List[str]: List of collection names
        """
        return self.client.list_collections()

def get_collection_stats(collection):
    sources = set()
    for doc in collection["metadatas"]:
        sources.add(doc.get("source", "Unknown"))

    # Count documents per source
    source_counts = {}
    for doc in collection["metadatas"]:
        source = doc.get("source", "Unknown")
        source_counts[source] = source_counts.get(source, 0) + 1

    # Create and display summary stats
    st.write(f"Found {len(collection['metadatas'])} documents from {len(sources)} sources")

    # Create dataframe and display as table
    source_df = pd.DataFrame(
        [[source, count] for source, count in source_counts.items()],
        columns=["Source", "Number of Documents"]
    )
    return st.dataframe(source_df)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

# Create a section for creating new collections
with st.expander("Create New Collection"):
    new_collection_name = st.text_input(
        "New Collection Name",
        placeholder="Enter a name for the new collection",
        help="Collection names will be sanitized to meet Chroma requirements"
    )

    create_collection = st.button("Create Collection")

    if create_collection and new_collection_name:
        # Sanitize the collection name
        sanitized_name = ChromaDocStore()._sanitize_collection_name(new_collection_name)

        try:
            # Create a new Chroma collection
            new_vector_store = Chroma(
                collection_name=sanitized_name,
                embedding_function=embeddings,
                persist_directory="langchain"
            )
            st.success(f"Successfully created collection: {sanitized_name}")

            # Force a page refresh to show the new collection
            st.rerun()
        except Exception as e:
            st.error(f"Error creating collection: {str(e)}")

# List and select collections
chroma = ChromaDocStore()
collections = chroma.list_collections()

if not collections:
    st.warning("No collections found. Create a new collection to get started.")
    st.stop()

# Add collection selection and management
col1, col2 = st.columns([3, 1])

with col1:
    selected_collection = st.selectbox("Select Collection", collections)

with col2:
    # Add delete collection button
    if st.button("Delete Collection", type="secondary"):
        st.session_state.show_delete_dialog = True

# Handle delete collection dialog
if "show_delete_dialog" not in st.session_state:
    st.session_state.show_delete_dialog = False

if st.session_state.get("show_delete_dialog", False):
    with st.form("delete_collection_form"):
        st.warning(f"Are you sure you want to delete collection '{selected_collection}'?")
        st.write("This action cannot be undone. All documents in this collection will be permanently deleted.")

        col1, col2 = st.columns([1, 1])
        with col1:
            confirm = st.form_submit_button("Delete Collection", type="primary")
        with col2:
            cancel = st.form_submit_button("Cancel")

        if confirm:
            try:
                # Delete the collection using LangChain Chroma
                client = chromadb.PersistentClient(path="langchain")
                client.delete_collection(name=selected_collection)
                st.session_state.show_delete_dialog = False
                st.success(f"Collection '{selected_collection}' has been deleted")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting collection: {str(e)}")

        if cancel:
            st.session_state.show_delete_dialog = False
            st.rerun()

# Initialize vector store with selected collection
vector_store = Chroma(
    collection_name=str(selected_collection),
    embedding_function=embeddings,
    persist_directory="langchain"
)

# Get collection data and display stats
col = vector_store.get()
get_collection_stats(col)

# Add search functionality
st.divider()
st.subheader("Search Collection")

search_query = st.text_input(
    "Search Query",
    placeholder="Enter your search query",
    help="Search for documents in the collection"
)

num_results = st.slider(
    "Number of Results",
    min_value=1,
    max_value=10,
    value=3,
    help="Number of results to return"
)

if search_query:
    with st.spinner("Searching..."):
        try:
            # Perform similarity search with score
            results = vector_store.similarity_search_with_score(
                query=search_query,
                k=num_results
            )

            # Display results
            st.write(f"Found {len(results)} results for '{search_query}'")

            for i, (doc, score) in enumerate(results):
                # Each result is a tuple of (Document, score)
                with st.expander(f"Result {i+1} - {doc.metadata.get('source', 'Unknown')}"):
                    st.write(f"**ID:** {doc.id if hasattr(doc, 'id') else 'N/A'}")
                    st.write(f"**Score:** {score:.4f}")  # Format score to 4 decimal places
                    st.write(f"**Source:** {doc.metadata.get('source', 'Unknown')}")

                    # Display document content
                    st.markdown("**Content:**")
                    st.markdown(doc.page_content)
        except Exception as e:
            st.error(f"Error searching collection: {str(e)}")

# Add a section for adding documents to the collection
st.divider()
st.subheader("Add Documents to Collection")

def process_document(uploaded_file) -> Tuple[List[Document], List[str]]:
    """Process a document and prepare it for adding to the collection.

    Args:
        uploaded_file: The uploaded file object

    Returns:
        Tuple containing list of Document objects and their IDs
    """
    with st.spinner("Loading and parsing document..."):
        file_name = uploaded_file.name
        # Save the file temporarily
        with open(f"{file_name}", "wb") as f:
            f.write(uploaded_file.getvalue())

        # Load the document
        try:
            loader = UnstructuredLoader(
                file_name,
                chunking_strategy="by_title",
                max_characters=1000,
                new_after_n_chars=500,
                combine_text_under_n_chars=200
            )
            raw_docs = loader.load()

            # Filter the metadata for all documents
            filtered_metadata_list = filter_complex_metadata(raw_docs)

            # Create Documents with filtered metadata
            docs = [Document(
                page_content=doc if isinstance(doc, str) else doc.page_content,
                metadata={
                    **doc.metadata,
                    "source": file_name,
                    "upload_date": datetime.utcnow().isoformat()
                },
                id=doc.metadata.get("element_id", f"{i}-{file_name}")
            ) for i, doc in enumerate(raw_docs)]

            ids = [doc.id for doc in docs]

            # Clean up the temporary file
            os.remove(file_name)

            return docs, ids
        except Exception as e:
            # Clean up the temporary file in case of error
            if os.path.exists(file_name):
                os.remove(file_name)
            st.error(f"Error processing document: {str(e)}")
            return [], []

# Add file uploader for adding documents to the selected collection
if selected_collection:
    uploader = st.file_uploader(
        f"Upload documents to add to '{selected_collection}' collection",
        accept_multiple_files=True,
        help="Supported formats depend on the UnstructuredLoader capabilities"
    )

    if uploader:
        all_docs = []
        all_ids = []
        success_count = 0

        # Process each uploaded file
        for file in uploader if isinstance(uploader, list) else [uploader]:
            docs, ids = process_document(file)
            if docs and ids:
                all_docs.extend(docs)
                all_ids.extend(ids)
                success_count += 1

        # Add documents to the collection if any were processed successfully
        if all_docs and all_ids:
            with st.spinner("Adding documents to collection..."):
                try:
                    vector_store.add_documents(documents=all_docs, ids=all_ids)
                    st.success(f"Successfully added {len(all_docs)} documents from {success_count} files to the collection")

                    # Refresh the collection data
                    col = vector_store.get()
                    get_collection_stats(col)
                except Exception as e:
                    st.error(f"Error adding documents to collection: {str(e)}")
else:
    st.info("Please select a collection first to add documents")

# Add a section for viewing and deleting documents in the collection
if selected_collection and col["ids"]:
    st.divider()
    st.subheader("Manage Documents in Collection")

    # Group documents by source
    doc_sources = {}
    for i, doc_id in enumerate(col["ids"]):
        source = col["metadatas"][i].get("source", "Unknown")
        if source not in doc_sources:
            doc_sources[source] = []
        doc_sources[source].append((doc_id, col["metadatas"][i]))

    # Display documents grouped by source
    for source, docs in doc_sources.items():
        with st.expander(f"{source} ({len(docs)} documents)"):
            for doc_id, metadata in docs:
                col1, col2 = st.columns([4, 1])

                # Display document info
                with col1:
                    st.write(f"**ID:** {doc_id}")
                    st.write(f"**Upload Date:** {metadata.get('upload_date', 'Unknown')}")

                    # Show a preview of the document content
                    if "page_content" in metadata:
                        preview = metadata["page_content"]
                        if len(preview) > 100:
                            preview = preview[:100] + "..."
                        st.write(f"**Preview:** {preview}")

                # Add delete button
                with col2:
                    if st.button("Delete", key=f"delete_{doc_id}"):
                        try:
                            # Delete the document from the collection
                            vector_store.delete(ids=[doc_id])
                            st.success(f"Document deleted successfully")

                            # Refresh the collection data
                            col = vector_store.get()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting document: {str(e)}")

                st.divider()



