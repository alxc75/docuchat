import streamlit as st
from st_pages import Page, show_pages
import tiktoken
from openai import OpenAI, OpenAIError
from pages.settings import api_key
import math

st.set_page_config(page_title="DocuChat", page_icon=":speech_balloon:", layout="wide")

# Initialize the session key for the text. See the end of parse_document() for writing.
if "text" not in st.session_state:
    st.session_state["text"] = ""

# Create the navigation bar
show_pages(
    [
        Page("main.py", "Summary", ":house:"),
        Page("pages/1_chat.py", "Chat", ":speech_balloon:"),
        Page("pages/settings.py", "Settings", ":gear:"),
        Page("pages/3_faq.py", "Help & FAQ", ":question:")
    ]
)

# Current page sidebar
st.sidebar.title("Summary")
st.sidebar.markdown("""
Use this tab to get a quick summary of your uploaded document.\n
TODO: 
- [x] Create working summarizer
- [x] Add caching to the whole page. Switching between tabs should not refresh the page.
- [x] Add a token warning
- [x] Switch to the Chat API for larger models
- [x] Add model auto-selection
- [x] Add parsed text caching. Need to wrap the text parsing in a function first, then store it in the session storage. Will be necessary for Chat Mode.
""")

# Top level greeting
title, modeToggle = st.columns(2)
title.title("DocuChat")
modeToggle.toggle("Advanced Mode", value=False, key="simple_mode", disabled=True, help="Coming soon!")
st.markdown("""
Welcome to DocuChat, your smart knowledge assistant.

Upload a document and a summary will be generated below. Use the Chat tab to ask questions about the document.
""")
st.header(' ') # Add some space

# Maximum number of tokens to generate
gen_max_tokens = 500

# Upload file
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx"], help="Accepts PDF and Word documents.")

@st.cache_data(show_spinner=True, persist=True)
def parse_document(uploaded_file):
    text = ''
    tokens = 0
    if uploaded_file is None: # Prevent error message when no file is uploaded
        return text, tokens, None
    else:
        name = uploaded_file.name
        # Check the extension and load the appropriate library
        if name.endswith(".pdf"):
            import PyPDF2
            pdfReader = PyPDF2.PdfReader(uploaded_file)
            for page in range(len(pdfReader.pages)):
                page_obj = pdfReader.pages[page]
                text += page_obj.extract_text()

        elif name.endswith(".docx"):
            import docx2txt
            text = docx2txt.process(uploaded_file)

        # Count the number of tokens in the document
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        output = encoding.encode(text)
        tokens = len(encoding.encode(text))

        # Choose the right model based on the number of tokens. GPT-3.5-Turbo only.
        if tokens == 0:
            model = None
        elif tokens <= 4096 - gen_max_tokens:
            model = "gpt-3.5-turbo"
        elif tokens <= 16385 - gen_max_tokens:
            model = "gpt-3.5-turbo-16k"
        else:
            divider = math.ceil(tokens / 16385)
            st.error(f"Your document is too long! You need to choose a smaller document or divide yours in {divider} parts.")
            model = None
            st.stop()

        # Display the token count and model used inside a collapsible container
        with st.expander("Show details"):
            st.write(f"Number of tokens: {tokens}")
            st.write(f"Using model: {model}")

        # Save the text to the session state
        st.session_state["text"] = text

        return text, tokens, model

# Use the function to parse the uploaded file
text, tokens, model = parse_document(uploaded_file)


# Create the OpenAI request
client = OpenAI(api_key=api_key)
sys_prompt = ("You are an assistant designed to give summaries of uploaded documents. Your answers should be decently long, "
          "in the form of bullet points. Make sure to include every point discussed in the document. Being verbose is "
          "highly preferable compared to missing ideas in the document. Here is the document to recap:")

@st.cache_data(show_spinner=True, persist=True)
def generate_completion(text):
    if text == '':
        print("No document detected. No completion will be generated.")
        return ""

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            max_tokens=gen_max_tokens,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text}
            ]
        )
        st.markdown("## Summary")
        response_text = response.choices[0].message.content

        # Add session state to keep the output text if the user switches tabs
        if 'saved_text' in st.session_state:
            del st.session_state.saved_text
            st.session_state.saved_text = response_text
        else:
            st.session_state.saved_text = response_text
        st.cache_data.clear()

        return response_text

    except OpenAIError as e:
        print(f"An error occurred: {e}")
        return None


response_text = generate_completion(text)


output_wrapper = st.empty() # Create a wrapper around the output to allow for clearing it
# Add session state to keep the output text
if 'saved_text' not in st.session_state:
    output_wrapper.markdown(response_text)
else:
    output_wrapper.markdown(st.session_state.saved_text)

regen, clear = st.columns(2)
if len(response_text) > 0:
    if regen.button("Regenerate summary"):
        st.cache_data.clear()

    if clear.button("Clear summary"):
        del st.session_state.saved_text
        del st.session_state.text
        st.cache_data.clear()
        output_wrapper.empty()
        st.toast("Summary cleared!", icon="🔥")
        st.stop()