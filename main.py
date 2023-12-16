import streamlit as st
from st_pages import Page, show_pages
from helper import parse_document
from pages.summarizer import generate_completion

uploaded_file = None
def main():
    # Top level greeting
    title, modeToggle = st.columns(2)
    title.title("DocuChat")
    modeToggle.toggle("Advanced Mode", value=False, key="simple_mode", disabled=True, help="Coming soon!")
    st.markdown("""
    Welcome to DocuChat, your smart knowledge assistant.
    
    Upload a document and a summary will be generated below. Use the Chat tab to ask questions about the document. 
    See the FAQ page for more information.
    """)
    st.header(' ') # Add some space

    # Upload file
    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx"],
                                 help="Accepts PDF and Word documents.")
    
    if uploaded_file is not None:
        st.write("File uploaded successfully!")
        raw_text, tokens, model = parse_document(uploaded_file)
        if "text" not in st.session_state:
            st.session_state.text = raw_text
        else:
            st.session_state.text = raw_text
        if "tokens" not in st.session_state:
            st.session_state.tokens = tokens
        else:
            st.session_state.tokens = tokens
        if "model" not in st.session_state:
            st.session_state.model = model
        else:
            st.session_state.model = model

    tab_options = ["Summary", "Chat", "Settings"]
    active_tab = st.radio("Navigation", tab_options)

    # Render the selected tab
    if active_tab == "Summary":
        render_summary()

    return raw_text, tokens, model

# Create the navigation bar
show_pages(
    [
        Page("main.py", "Home", ":house:"),
        Page("pages/3_FAQ.py", "Help & FAQ", ":question:"),
        Page("pages/99_Local_Mode.py", "Local Mode", "💻")
    ]
)

# Current page sidebar
st.sidebar.title("Home")
st.sidebar.markdown("""
Welcome to DocuChat! Use this sidebar to move around the application.\n
""")


def render_summary():
    st.header("Summary")
    st.markdown("Use this tab to generate a quick summary of your document.")

   # Use the function to parse the uploaded file
    if "text" not in st.session_state:
        st.session_state.text = ""
    else:
        raw_text = st.session_state.text
    if "tokens" not in st.session_state:
        st.session_state.tokens = 0
    else:
        tokens = st.session_state.tokens
    if "model" not in st.session_state:
        st.session_state.model = None
    else:
        model = st.session_state.model

    # Summary container
    if raw_text is not None:
        response_text = generate_completion(raw_text, model)
    output_wrapper = st.empty() # Create a wrapper around the output to allow for clearing it

    st.write(response_text)
    # Add session state to keep the output text
    if 'saved_text' not in st.session_state:
        st.session_state.saved_text = response_text
        output_wrapper.markdown(response_text)
    else:
        output_wrapper.markdown(st.session_state.saved_text)

    st.session_state

    def regenerate_summary():
        st.cache_data.clear()
        output_wrapper.empty()


    def clear_summary():
        st.session_state.saved_text = ''
        output_wrapper.empty()
        st.toast("Summary cleared!", icon="🔥")

    # Add buttons to regenerate and clear the summary
    if len(response_text) > 0:
        st.sidebar.button("Regenerate summary", on_click=regenerate_summary)
        if st.sidebar.button("Clear summary", on_click=clear_summary):
            st.stop()

if __name__ == "__main__":
    main()