import streamlit as st
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import toml

from chroma_utils import ChromaDocStore

st.sidebar.title("LangChain")
st.sidebar.markdown("LangChain Loader & Search Demo")
st.title("LangChain")
st.divider()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

with st.spinner("Loading collection..."):
    chroma = ChromaDocStore()
    collections = chroma.list_collections()
    selected_collection = st.sidebar.selectbox("Select Collection", collections)
    embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

vector_store = Chroma(
    collection_name=str(selected_collection),
    embedding_function=embeddings,
    persist_directory="langchain"
)


secrets_path = ".streamlit/secrets.toml"
with open(secrets_path, "r") as f:
    secrets = toml.load(f)
default_model = secrets["ollama"]["default_model"]
llm = ChatOllama(
    model=default_model,
    temperature=0.3,
    num_predict=500
)



def llm_response(llm, messages):
    for chunk in llm.stream(messages):
        yield(chunk.text())

if prompt := st.chat_input("What do you want to know about these documents?"):
    results = vector_store.similarity_search(str(prompt), 10)
    results_contents = [doc.page_content for doc in results]

    st.session_state.messages.append({"role": "system", "content": f"You are a retrieval model. You have access to the most relevant results from a collection of document. Answer the user's question about these documents. Only base your answer on the following documents. If the question cannot be answered from the following documents, clearly state so. Here are the results: {results_contents}"})
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})


    response = llm_response(llm, st.session_state.messages)
    with st.chat_message("assistant"):
        st.write_stream(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})