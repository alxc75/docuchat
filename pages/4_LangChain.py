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
    # Only display messages that are not system messages
    if message["role"] != "system":
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
    """Stream the LLM response and collect the full text.

    Args:
        llm: The language model to use
        messages: The conversation history

    Returns:
        The complete response text
    """
    full_response = ""
    for chunk in llm.stream(messages):
        chunk_text = chunk.text()
        full_response += chunk_text
        yield chunk_text  # Still yield chunks for streaming display
    return full_response  # Return the complete text after streaming

if prompt := st.chat_input("What do you want to know about these documents?"):
    # Only process the prompt if it contains non-whitespace characters
    if prompt.strip():
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Perform similarity search for the current question
        results = vector_store.similarity_search(str(prompt), 10)
        results_contents = [doc.page_content for doc in results]

        # Create system message with context
        system_message = {"role": "system", "content": f"You are a retrieval model. You have access to the most relevant results from a collection of document. Answer the user's question about these documents. Only base your answer on the following documents. If the question cannot be answered from the following documents, clearly state so. Here are the results: {results_contents}"}

        # Check if there's already a system message and update it
        system_message_index = next((i for i, msg in enumerate(st.session_state.messages)
                                    if msg["role"] == "system"), None)
        if system_message_index is not None:
            # Update existing system message
            st.session_state.messages[system_message_index] = system_message
        else:
            # Add new system message at the beginning
            st.session_state.messages.insert(0, system_message)


        # Create a generator for streaming and capture the full response
        response_generator = llm_response(llm, st.session_state.messages)
        full_response = ""

        # Display the streaming response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            for chunk in response_generator:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        # Add assistant response to chat history with the complete text
        st.session_state.messages.append({"role": "assistant", "content": full_response})