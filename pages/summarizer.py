import streamlit as st
import tiktoken
from openai import OpenAI, OpenAIError
from helper import api_key, parse_document, gen_max_tokens
import math


# Initialize the session key for the text. See the end of parse_document() for writing.
if "text" not in st.session_state:
    st.session_state["text"] = ""





# Create the OpenAI request
client = OpenAI(api_key=api_key)
sys_prompt = ("You are an assistant designed to give summaries of uploaded documents. Your answers should be decently long, "
          "in the form of bullet points. Make sure to include every point discussed in the document. Being verbose is "
          "highly preferable compared to missing ideas in the document. Here is the document to recap:")

@st.cache_data(show_spinner=True, persist=True)
def generate_completion(text, model):
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
            st.session_state.saved_text = response_text
        else:
            st.session_state.saved_text = response_text
        st.cache_data.clear()

        print(response_text)
        return response_text

    except OpenAIError as e:
        print(f"An error occurred: {e}")
        return None


# ------------------- LICENSE -------------------
# Docuchat, a smart knowledge assistant for your documents.
# Copyright © 2023 xTellarin
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