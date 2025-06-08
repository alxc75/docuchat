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
DocuChat is a locally-hosted application to summarize and chat with your documents. You can create collections of multiple documents and switch between collections at any time. Use the OpenAI API or run models
locally for 100% free usage.
""")

st.markdown("""
## How do I use it?
To get started, enter your OpenAI API key in the Settings tab. If you don't have one, get it [here](https://platform.openai.com/api-keys).
Your key is safe and will never leave your device. Neither I nor OpenAI have access to it.
Alternatively, install [Ollama](https://ollama.com/) then head to the Settings tab and toggle Local Mode.\n
Then, upload one or more documents in the Collections tab to query your documents.\n
""")

st.markdown("""
## What are Collections?
Colections are groups of documents that you can create and switch between at any time. You can create a collection by uploading documents in the Collections tab. You can upload various types of documents (PDFs, Powerpoint Presentations, Word Documents, CSV files, etc) but note that PDFs are the recommended format. You can add or remove documents from a collection after it has been created. You can also do a simple semantic query on a collection to see the most relevant paragraphs that will be fed to the LLM for a given query if you'd like.
""")

st.markdown("""
## What is Local Mode?
Local Mode is a feature that allows you to run models locally for 100% free usage using [Ollama](https://ollama.com/). You don't need an OpenAI API key to use it so DocuChat becomes completely free. To use it, download Ollama and a model via its interface and you're good to go. Docuchat will let you know if Ollama isn't running. If you don't know what model to use, DocuChat will automatically recommend a model that you can download in one click.\n
Note however that you still need a decently fast computer. We selected a base model with low requirements but it still needs a modern CPU and at least 8GB of RAM (16GB recommended).
If the answers are taking too long to generate, try using the OpenAI API instead. We selected the `gpt-4.1-mini` model that's super fast and cheap.
""")


st.markdown("""
If you have any suggestions or a bug you would like to report, please let me know on [GitHub](https://github.com/xTellarin/docuchat/tree/main)!
""")


st.markdown("#") # Spacer
st.markdown("#") # Spacer
st.markdown("---") # Divider

st.markdown(f"""
### Copyright Notice
Docuchat, a smart knowledge assistant for your documents.\n
Copyright © {year} alxc75\n
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