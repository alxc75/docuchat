import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import re
import os
from sentence_transformers import SentenceTransformer
import pandas as pd


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

chroma = ChromaDocStore()
collections = chroma.list_collections()
selected_collection = st.selectbox("Select Collection", collections)
embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
vector_store = Chroma(
    collection_name=str(selected_collection),
    embedding_function=embeddings,
    persist_directory="langchain"
    )


col = vector_store.get()

get_collection_stats(col)


