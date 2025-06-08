import streamlit as st
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import toml

from chroma_utils import ChromaDocStore
from helper import api_key, ollama_flag

st.sidebar.title("DocuChat")
st.sidebar.markdown("Chat with your documents.")
st.title("DocuChat")
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
    # Get the list of collection objects
    collection_objects = chroma.list_collections()
    # Extract just the names into a simple list for the selectbox
    collections = [c.name for c in collection_objects]

    selected_collection = st.sidebar.selectbox("Select Collection", collections)

    # Add configurable number of results in sidebar
    num_results = st.sidebar.slider(
        "Number of Results",
        min_value=1,
        max_value=20,
        value=10,
        help="Number of documents to retrieve from vector store for context"
    )

    embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

vector_store = Chroma(
    collection_name=str(selected_collection),
    embedding_function=embeddings,
    persist_directory="langchain"
)


# Initialize LLM based on Local Mode setting
if ollama_flag == 1:  # Local Mode enabled - use Ollama
    secrets_path = ".streamlit/secrets.toml"
    with open(secrets_path, "r") as f:
        secrets = toml.load(f)
    default_model = secrets["ollama"]["default_model"]

    # Debug logging to validate the model name
    print(f"DEBUG: default_model value: '{default_model}'")
    print(f"DEBUG: default_model length: {len(default_model)}")

    # Validate that the model name is not empty
    if not default_model or default_model.strip() == "":
        st.error("❌ Error: No model specified in secrets.toml. Please set a valid Ollama model name in the 'default_model' field.")
        st.info("💡 Example models: llama2, mistral, codellama, phi, gemma")
        st.stop()

    llm = ChatOllama(
        model=default_model,
        temperature=0.3,
        num_predict=500
    )
else:  # Local Mode disabled - use OpenAI
    # Validate that the API key is not empty
    if not api_key or api_key.strip() == "":
        st.error("❌ Error: No OpenAI API key found. Please set your API key in the Settings tab.")
        st.info("💡 You can get your API key at https://platform.openai.com/api-keys")
        st.stop()

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=api_key
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
        results = vector_store.similarity_search(str(prompt), num_results)
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

def clear_all():
    st.session_state.messages = []
    st.session_state.selected_collection = None
    st.session_state.collection_selector = "None"
    st.rerun()

if len(st.session_state.messages) > 0:
    st.sidebar.button('Clear All', on_click=clear_all)