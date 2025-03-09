import streamlit as st
from langchain_unstructured import UnstructuredLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_ollama import ChatOllama
import toml
import os

prompt = "What is the dataset used by the paper's authors?"

st.sidebar.title("LangChain")
st.sidebar.markdown("LangChain Loader & Search Demo")
st.title("LangChain")
st.divider()

uploader = st.file_uploader("Upload a docsument")
if not uploader:
    st.stop()

with st.spinner("Loading and parsing document..."):
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

with st.spinner("Embedding documents..."):
    # Embed the docsument
    embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

    # Verify the embedding lengths
    vector_1 = embeddings.embed_query(docs[0].page_content)
    vector_2 = embeddings.embed_query(docs[1].page_content)
    assert len(vector_1) == len(vector_2) # Raises an AssertionError if the lengths are not equal


# Initialize the Chroma engine
vector_store = Chroma(
    collection_name="langchain",
    embedding_function=embeddings,
    persist_directory="langchain"
    )
# Index the docsuments
with st.spinner("Indexing documents..."):
    vector_store.add_documents(documents=docs, ids=ids)
    st.toast("Documents indexed successfully")

results = vector_store.similarity_search(str(prompt))
results_contents = [doc.page_content for doc in results]
# st.write([doc.page_content for doc in results]) # Uncomment to see the retrieval results

secrets_path = ".streamlit/secrets.toml"
with open(secrets_path, "r") as f:
    secrets = toml.load(f)
default_model = secrets["ollama"]["default_model"]
llm = ChatOllama(
    model=default_model,
    temperature=0.3,
    num_predict=500
)

messages = [
    ("system", f"You are a retrieval model. You have access to the most relevant results from a collection of document. Answer the user's question about these documents. Only base your answer on the following documents. If the question cannot be answered from the following documents, clearly state so. Here are the results: {results_contents}"),
    ('human', str(prompt))
]

def llm_response(llm, messages):
    for chunk in llm.stream(messages):
        yield(chunk.text())

st.write_stream(llm_response(llm, messages))