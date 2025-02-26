import streamlit as st
import datetime
year = datetime.datetime.now().year

st.sidebar.title("Help & FAQ")
st.sidebar.markdown("Use this tab to get help and answers to frequently asked questions.")
st.title("Help & FAQ")
st.markdown("Get answers to your questions about DocuChat.")
st.markdown("---") # Divider

st.markdown("""
## What is DocuChat?
DocuChat is a locally-hosted application to summarize and chat with your documents. Use the OpenAI API or run models
locally for 100% free usage. You can even query multiple documents thanks to state-of-the-art RAG integrations (coming soon!).
""")

st.markdown("""
## How do I use it?
To get started, enter your OpenAI API key in the Settings tab. If you don't have one, get it [here](https://platform.openai.com/api-keys).
Your key is safe and will never leave your device. Neither I nor OpenAI have access to it.
Alternatively, head to the Local Mode tab in the sidebar to install the required tools and toggle Local Mode in the Settings.\n
Then, upload a document in the Summary tab to get a one-click summary. Alternatively you can use the Chat tab to ask questions about your document.\n
*Did you know? A document uploaded in the Summary tab is automatically shared to the Chat tab and vice-versa. Upload a new document to start over.*
""")

st.markdown("""
## What is Local Mode?
Local Mode is a feature that allows you to run models locally for 100% free usage. You don't need an OpenAI API key to use it so DocuChat becomes completely free.\n
Note however that you still need a decently fast computer. We selected a base model with low to midrange requirements but it still needs a decent CPU and at least 8GB of RAM (16GB recommended).
If the answers are taking too long to generate, try using the OpenAI API instead.
""")

st.markdown("""
## What's on the roadmap?
DocuChat is still in early development. Here are some of the features I'm working on:\n
- Local mode: Run models locally for 100% free usage, no OpenAI API key required.
- Advanced mode: Upload multiple documents and query them with citations thanks to state-of-the-art machine learning techniques.

If you have any suggestions or a bug you would like to report, please let me know on [GitHub](https://github.com/xTellarin/docuchat/tree/main)!
Alternatively, you can reach me on Discord at `tellarin` or by [email](mailto:tellarin.dev@gmail.com).
""")


st.markdown("#") # Spacer
st.markdown("#") # Spacer
st.markdown("#") # Spacer
st.markdown("---") # Divider

st.markdown(f"""
### Copyright Notice
Docuchat, a smart knowledge assistant for your documents.\n
Copyright © {year} xTellarin\n
Licensed under GNU GPL Version 3\n
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
""")

# ------------------- LICENSE -------------------
# Docuchat, a smart knowledge assistant for your documents.
# Copyright © 2025 alxc75
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see https://www.gnu.org/licenses/.