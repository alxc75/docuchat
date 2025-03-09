import streamlit as st
import chromadb
from chromadb.config import Settings
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_unstructured import UnstructuredLoader
from typing import List, Tuple
import re
import os
from sentence_transformers import SentenceTransformer
import pandas as pd
from datetime import datetime

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