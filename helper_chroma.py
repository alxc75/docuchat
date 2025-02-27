import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

class ChromaDocStore:
    def __init__(self, persist_dir: str = "./db/chroma"):
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

    def create_collection(self, name: str) -> chromadb.Collection:
        """Create a new collection or get existing one.

        Args:
            name: Name of the collection

        Returns:
            chromadb.Collection: The created/retrieved collection
        """
        name = self._sanitize_collection_name(name)
        try:
            return self.client.create_collection(
                name=name,
                metadata={"created_at": datetime.utcnow().isoformat()}
            )
        except ValueError:  # Collection already exists
            return self.client.get_collection(name=name)

    def process_document(self, text: str, chunk_size: int = 500) -> List[str]:
        """Process document text into chunks.

        Args:
            text: Document text to process
            chunk_size: Size of each chunk in characters

        Returns:
            List[str]: List of text chunks
        """
        # Simple character-based chunking for now
        # TODO: Implement more sophisticated chunking (e.g., sentence/paragraph based)
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
        return chunks

    def add_document(
        self,
        collection_name: str,
        text: str,
        metadata: Dict,
        doc_id: Optional[str] = None
    ) -> str:
        """Add a document to a collection.

        Args:
            collection_name: Name of the collection
            text: Document text
            metadata: Document metadata (filename, upload date, etc.)
            doc_id: Optional document ID

        Returns:
            str: Document ID
        """
        collection = self.create_collection(collection_name)

        # Process document into chunks
        chunks = self.process_document(text)

        # Generate embeddings for chunks
        embeddings = self.embedding_model.encode(chunks).tolist()

        # Generate chunk IDs if doc_id provided
        if doc_id:
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        else:
            ids = [f"chunk_{i}" for i in range(len(chunks))]

        # Add chunks to collection
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=[{**metadata, "chunk_index": i} for i in range(len(chunks))]
        )

        return doc_id or ids[0].split("_chunk_")[0]

    def query_documents(
        self,
        collection_name: str,
        query: str,
        n_results: int = 3
    ) -> Dict:
        """Query documents in a collection.

        Args:
            collection_name: Name of the collection
            query: Query text
            n_results: Number of results to return

        Returns:
            Dict: Query results with documents and metadata
        """
        collection_name = self._sanitize_collection_name(collection_name)
        collection = self.client.get_collection(name=collection_name)

        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()

        # Query the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        return results
    def list_collections(self) -> List[str]:
        """List all collections.

        Returns:
            List[str]: List of collection names
        """
        return self.client.list_collections()

    def get_collection_info(self, collection_name: str) -> Dict:
        """Get information about a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dict: Collection metadata and document count
        """
        # Sanitize the collection name
        collection_name = self._sanitize_collection_name(collection_name)

        try:
            # Get the collection
            collection = self.client.get_collection(name=collection_name)

            # Get collection metadata
            metadata = collection.metadata

            # Count unique documents by extracting document IDs from chunk IDs
            all_ids = collection.get(include=[])["ids"]
            doc_ids = set()

            for chunk_id in all_ids:
                # Extract document ID from chunk ID (format: "{doc_id}_chunk_{i}")
                if "_chunk_" in chunk_id:
                    doc_id = chunk_id.split("_chunk_")[0]
                    doc_ids.add(doc_id)

            # Get total chunks count
            total_chunks = len(all_ids)

            # Return combined information
            return {
                "name": collection_name,
                "created_at": metadata.get("created_at", "Unknown"),
                "document_count": len(doc_ids),
                "chunk_count": total_chunks,
                "documents": list(doc_ids)
            }
        except Exception as e:
            return {
                "name": collection_name,
                "error": str(e)
            }

    def list_documents(self, collection_name: str) -> List[Dict]:
        """List all documents in a collection with their metadata.

        Args:
            collection_name: Name of the collection

        Returns:
            List[Dict]: List of documents with metadata
        """
        # Sanitize the collection name
        collection_name = self._sanitize_collection_name(collection_name)

        try:
            # Get the collection
            collection = self.client.get_collection(name=collection_name)

            # Get all chunk IDs and metadata
            result = collection.get(include=["metadatas"])
            chunk_ids = result["ids"]
            metadatas = result["metadatas"]

            # Group chunks by document ID
            documents = {}

            for i, chunk_id in enumerate(chunk_ids):
                # Extract document ID from chunk ID
                if "_chunk_" in chunk_id:
                    doc_id = chunk_id.split("_chunk_")[0]
                    metadata = metadatas[i]

                    # Store unique document metadata
                    if doc_id not in documents:
                        documents[doc_id] = {
                            "id": doc_id,
                            "filename": metadata.get("filename", "Unknown"),
                            "upload_date": metadata.get("upload_date", "Unknown"),
                            "token_count": metadata.get("token_count", 0),
                            "model": metadata.get("model", "Unknown"),
                            "chunk_count": 0
                        }

                    # Count chunks per document
                    documents[doc_id]["chunk_count"] += 1

            return list(documents.values())
        except Exception as e:
            return [{
                "error": str(e)
            }]

    def rename_collection(self, old_name: str, new_name: str) -> str:
        """Rename a collection.

        Args:
            old_name: Current collection name
            new_name: New collection name

        Returns:
            str: Sanitized new collection name
        """
        # Sanitize both names
        old_name = self._sanitize_collection_name(old_name)
        new_name = self._sanitize_collection_name(new_name)

        # Check if source collection exists
        try:
            old_collection = self.client.get_collection(name=old_name)
        except Exception as e:
            raise ValueError(f"Source collection not found: {str(e)}")

        # Check if target name is different
        if old_name == new_name:
            return old_name

        # Check if target collection already exists
        try:
            self.client.get_collection(name=new_name)
            raise ValueError(f"Collection '{new_name}' already exists")
        except ValueError as e:
            # Re-raise if it's our error about existing collection
            if "already exists" in str(e):
                raise
            # Otherwise, the collection doesn't exist, which is what we want
            pass

        # Create new collection with metadata from old one
        new_collection = self.client.create_collection(
            name=new_name,
            metadata=old_collection.metadata
        )

        # Get all data from old collection
        data = old_collection.get(include=["embeddings", "documents", "metadatas"])

        # If there's data to transfer
        if data["ids"]:
            # Add all data to new collection
            new_collection.add(
                ids=data["ids"],
                embeddings=data["embeddings"],
                documents=data["documents"],
                metadatas=data["metadatas"]
            )

        # Delete old collection
        self.client.delete_collection(name=old_name)

        return new_name

    def delete_document(self, collection_name: str, doc_id: str) -> bool:
        """Delete a specific document from a collection.

        Args:
            collection_name: Name of the collection
            doc_id: Document ID to delete

        Returns:
            bool: Success status
        """
        # Sanitize collection name
        collection_name = self._sanitize_collection_name(collection_name)

        try:
            # Get the collection
            collection = self.client.get_collection(name=collection_name)

            # Get all chunk IDs
            chunk_ids = collection.get(include=[])["ids"]

            # Find chunks belonging to this document
            doc_chunks = []
            for chunk_id in chunk_ids:
                if chunk_id.startswith(f"{doc_id}_chunk_"):
                    doc_chunks.append(chunk_id)

            # If chunks found, delete them
            if doc_chunks:
                collection.delete(ids=doc_chunks)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False

    def delete_collection(self, name: str) -> None:
        """Delete a collection.

        Args:
            name: Name of the collection
        """
        name = self._sanitize_collection_name(name)
        self.client.delete_collection(name=name)

def load_chroma():
    from helper_chroma import ChromaDocStore
    # Initialize collection selector state
    if "selected_collection" not in st.session_state:
        st.session_state.selected_collection = None

    # Get available collections
    doc_store = ChromaDocStore()
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
        st.sidebar.info("No collections available. Upload a document in the Collections tab to create one.")

    return doc_store