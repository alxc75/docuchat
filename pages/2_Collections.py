import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb

from chroma_utils import process_document, get_collection_stats, ChromaDocStore

st.sidebar.title("Collections")
st.sidebar.markdown("Manage your document collections")
st.title("Collections")


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

with st.spinner("Loading Document Collections..."):
    # List and select collections
    chroma = ChromaDocStore()
    # Get the list of collection objects
    collection_objects = chroma.list_collections()
    # Extract just the names into a simple list for the selectbox
    collections = [c.name for c in collection_objects]

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

# Add a section for adding documents to the collection
st.divider()
st.subheader("Add Documents to Collection")


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
            # Add delete source button at the top of each source group
            if st.button("Delete Source", key=f"delete_source_{source}", type="secondary"):
                try:
                    # Get all document IDs for this source
                    source_doc_ids = [doc_id for doc_id, _ in docs]

                    # Delete all documents from this source
                    vector_store.delete(ids=source_doc_ids)
                    st.success(f"Successfully deleted all {len(source_doc_ids)} documents from '{source}'")

                    # Refresh the collection data
                    col = vector_store.get()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting documents: {str(e)}")

            # Display a sample of documents (first 3)
            st.write("**Sample documents:**")
            for i, (doc_id, metadata) in enumerate(docs[:3]):
                st.write(f"**Document {i+1}:**")
                st.write(f"ID: {doc_id}")
                st.write(f"Upload Date: {metadata.get('upload_date', 'Unknown')}")

                # Show a preview of the document content
                if "page_content" in metadata:
                    preview = metadata["page_content"]
                    if len(preview) > 100:
                        preview = preview[:100] + "..."
                    st.write(f"Preview: {preview}")

                if i < 2 and i < len(docs) - 1:  # Add divider between samples, but not after the last one
                    st.divider()

            # Show message if there are more documents
            if len(docs) > 3:
                st.write(f"... and {len(docs) - 3} more documents")



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