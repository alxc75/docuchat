# This file is a collection of helper functions for the Docuchat Streamlit app that shouldn't be written elsewhere.
# Import this file as a module to use the functions.

import os
import json
import streamlit as st
import tiktoken
import math

# Check whether the userinfo.json file exists
if os.path.exists("userinfo.json"):
    # Check whether the API key is set
    with open("userinfo.json", "r") as f:
        userinfo = json.load(f)
        if "api_key" in userinfo:
            api_key = userinfo["api_key"]
        else:
            api_key = ""

# If the userinfo.json file does not exist, create it
else:
    with open("userinfo.json", "w") as f:
        userinfo = {}
        api_key = ""
        json.dump(userinfo, f, indent=4)



# Maximum number of tokens to generate
gen_max_tokens = 500


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
        elif tokens <= 16385 - gen_max_tokens:
            model = "gpt-3.5-turbo-1106"
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