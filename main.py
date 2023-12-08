import streamlit as st
from st_pages import Page, show_pages
import tiktoken
from openai import OpenAI, OpenAIError
from pages.settings import api_key

show_pages(
    [
        Page("main.py", "Summary", ":house:"),
        Page("pages/1_chat.py", "Chat", ":speech_balloon:"),
        Page("pages/settings.py", "Settings", ":gear:"),
        Page("pages/3_faq.py", "Help & FAQ", ":question:")
    ]
)


# Top level greeting
title, modeToggle = st.columns(2)
title.title("DocuChat")
modeToggle.toggle("Advanced Mode", value=False, key="simple_mode", disabled=True, help="Coming soon!")
st.markdown("""
Welcome to DocuChat, your smart knowledge assistant.
""")

# Navigation
st.sidebar.title("Summary")
st.sidebar.markdown("Use this tab to get a quick summary of your uploaded document.")

# Upload file
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx"], help="Accepts PDF and Word documents.")
text = ''
if uploaded_file is not None: # Prevent error message when no file is uploaded
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

    # Create a st.success and make it disappear after 1 second with .empty()
    # success = st.success("File uploaded successfully!")
    # import time
    # time.sleep(3)
    # success.empty()

    # Count the number of tokens in the document
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    output = encoding.encode(text)
    tokens = len(encoding.encode(text))
    st.write(f"Number of tokens: {tokens}")


# Create the OpenAI request
client = OpenAI(api_key=api_key)
prompt = ("You are an assistant designed to give summaries of uploaded documents. Your answers should be decently long, "
          "in the form of bullet points. Make sure to include every point discussed in the document. Being verbose is "
          "highly preferable compared to missing ideas in the document. Here is the document to recap:" + text)

@st.cache_data
def generate_completion(prompt):
    if text == '':
        print("No document detected. No completion will be generated.")
        return ""

    try:
        response = client.completions.create(
            prompt=prompt,
            model="gpt-3.5-turbo-instruct",
            temperature=0.5,
            max_tokens=2000
        )
        st.markdown("## Summary")
        response_text = response.choices[0].text
        return response_text


    except OpenAIError as e:
        print(f"An error occurred: {e}")
        return None



response_text = generate_completion(prompt)
st.markdown(response_text)






