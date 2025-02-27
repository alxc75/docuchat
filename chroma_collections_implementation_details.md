# Chroma Collections Implementation Details

Based on our enhancement plan and analysis of the existing codebase, this document provides detailed implementation specifications for each component. This will serve as a reference when implementing the features.

## 1. ChromaDocStore Class Extensions

### 1.1 Getting Collection Information

```python
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
```

### 1.2 Listing Documents in a Collection

```python
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
```

### 1.3 Renaming a Collection

```python
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
```

### 1.4 Deleting a Document

```python
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
```

## 2. Multiple File Upload Processing

### 2.1 Update parse_document Function

```python
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

    if uploaded_file is None:
        return text, tokens, None, None

    name = uploaded_file.name

    # Processing logic (unchanged)
    # ...

    # Create metadata
    metadata = {
        "filename": name,
        "upload_date": datetime.utcnow().isoformat(),
        "token_count": tokens,
        "model": model
    }

    # Use provided collection_name or sanitized filename
    coll_name = collection_name if collection_name else name

    # Store document in Chroma
    if text.strip():
        doc_store.add_document(
            collection_name=coll_name,
            text=text,
            metadata=metadata,
            doc_id=name  # Use filename as document ID
        )

    return text, tokens, model, metadata
```

### 2.2 Add Multiple File Processing Function

```python
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
```

## 3. UI Updates in Collections.py

### 3.1 Collection Naming Input

```python
# Add custom collection name input
custom_collection_name = st.text_input(
    "Collection Name (optional)",
    placeholder="Enter a name for your collection",
    help="If not provided, the first filename will be used"
)
```

### 3.2 Multiple File Upload Processing

```python
# Process uploaded files if present
if uploaded_file:
    with st.status("Processing document(s)...") as status:
        if isinstance(uploaded_file, list):  # Multiple files
            results = process_multiple_files(uploaded_file, custom_collection_name)
            if results["success_count"] > 0:
                status.update(label=f"Processed {results['success_count']} documents successfully")
                st.success(f"Added {results['success_count']} documents to collection '{results['collection_name']}'")

                # Set this as the active collection
                st.session_state.selected_collection = results["collection_name"]

                # Show processing details
                with st.expander("Processing Details"):
                    st.write(f"Total tokens: {results['total_tokens']}")
                    st.write("Processed files:")
                    for file in results["processed_files"]:
                        st.write(f"- {file['filename']}: {file['tokens']} tokens")

                    if results["failed_files"]:
                        st.error("Failed files:")
                        for file in results["failed_files"]:
                            st.write(f"- {file}")
            else:
                st.error("No documents were processed successfully")
        else:  # Single file (backward compatibility)
            # Existing single file logic
            parsed_text, tokens, model = parse_document(uploaded_file)
            if model:  # Document was processed successfully
                st.success(f"Document '{uploaded_file.name}' processed and stored")
                # Set this as the active collection
                st.session_state.selected_collection = uploaded_file.name
```

### 3.3 Collection Details View

```python
# Display collection details if one is selected
if st.session_state.selected_collection:
    collection_name = st.session_state.selected_collection

    # Create tabs for collection information
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader(f"Collection: {collection_name}")

    with col2:
        # Add rename collection button
        if st.button("Rename Collection"):
            st.session_state.show_rename_dialog = True

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

            if submit and new_name != collection_name:
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

    # Get collection info
    collection_info = doc_store.get_collection_info(collection_name)

    # Display collection metadata
    st.write(f"Created: {collection_info.get('created_at', 'Unknown')}")
    st.write(f"Documents: {collection_info.get('document_count', 0)}")
    st.write(f"Chunks: {collection_info.get('chunk_count', 0)}")

    # Display documents in the collection
    st.subheader("Documents")
    documents = doc_store.list_documents(collection_name)

    if not documents:
        st.info("No documents found in this collection")
    else:
        for doc in documents:
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
```

### 3.4 Upload to Existing Collection

```python
# Add "Upload to This Collection" option
if st.session_state.selected_collection:
    st.subheader("Add Documents to Collection")

    upload_to_current = st.file_uploader(
        f"Upload additional documents to '{st.session_state.selected_collection}'",
        type=["pdf", "docx"],
        help="Adds documents to the currently selected collection",
        key="additional_upload",
        accept_multiple_files=True
    )

    if upload_to_current:
        with st.status("Adding documents to collection...") as status:
            results = process_multiple_files(
                upload_to_current,
                st.session_state.selected_collection
            )

            if results["success_count"] > 0:
                status.update(label=f"Added {results['success_count']} documents to collection")
                st.success(f"Added {results['success_count']} documents to '{st.session_state.selected_collection}'")
                st.rerun()
            else:
                st.error("No documents were added successfully")
```

## 4. Update Initialization for Collection State

```python
# Initialize collection-related state
if "selected_collection" not in st.session_state:
    st.session_state.selected_collection = None

if "show_rename_dialog" not in st.session_state:
    st.session_state.show_rename_dialog = False
```

## Implementation Order

I recommend implementing these changes in the following order:

1. First, extend the ChromaDocStore class with new methods
2. Update the document processing functions to support multiple files
3. Update the Collections UI to include new features
4. Add error handling and validation
5. Test with existing collections for backward compatibility

With these detailed specifications, a developer can implement the enhancements to the Chroma Collections functionality while maintaining compatibility with the existing application.