import streamlit as st
from langchain_unstructured import UnstructuredLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
import os


st.sidebar.title("LangChain")
st.sidebar.markdown("LangChain Loader & Search Demo")
st.title("LangChain")
st.divider()

uploader = st.file_uploader("Upload a docsument")
if uploader:
    file_name = uploader.name
    # Save the file temporarily
    with open(f"{file_name}", "wb") as f:
        f.write(uploader.getvalue())
    # Load the docsument
    loader = UnstructuredLoader(file_name,
                                chunking_strategy="by_title",
                                max_characters=1000,
                                new_after_n_chars=500,
                                combine_text_under_n_chars=200)
    raw_docs = loader.load()
    # First filter the metadata for all documents
    filtered_metadata_list = filter_complex_metadata(raw_docs)

    # Create Documents with filtered metadata
    docs = [Document(
        page_content=doc if isinstance(doc, str) else doc.page_content,
        metadata=doc.metadata,
        # id=str(i)+"-"+file_name
        id = doc.metadata.get("element_id", str(i)+"-"+file_name)
    ) for i, doc in enumerate(raw_docs)]

    ids = [doc.id for doc in docs]
    doc_source = docs[0].metadata.get("source", "Unknown")
    os.remove(file_name)
    st.success("document loaded successfully, embedding...")

    # Embed the docsument
    embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

    # Verify the embedding lengths
    vector_1 = embeddings.embed_query(docs[0].page_content)
    vector_2 = embeddings.embed_query(docs[1].page_content)
    assert len(vector_1) == len(vector_2) # Raises an AssertionError if the lengths are not equal
    st.success("Embeddings generated successfully.")


    # Initialize the Chroma engine
    vector_store = Chroma(
        collection_name="langchain",
        embedding_function=embeddings,
        persist_directory="langchain"
        )
    st.success("Chroma engine initialized successfully")
    # Index the docsuments
    with st.spinner("Indexing documents..."):
        vector_store.add_documents(documents=docs, ids=ids)
    st.success("Documents indexed successfully")

    results = vector_store.similarity_search(
        "Quelle est la rémunération annuelle?"
    )
    st.write([doc.page_content for doc in results])