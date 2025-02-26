import streamlit as st
import json
import os
from helper import api_key
import toml

st.sidebar.title("Settings")
st.sidebar.markdown("Use this tab to change your OpenAI API key.")
st.title("Settings")
st.markdown("Please enter your OpenAI API key below.")

# Update both st.secrets and the TOML file
secrets_path = ".streamlit/secrets.toml"
# Read existing secrets
with open(secrets_path, "r") as f:
    secrets = toml.load(f)



### OpenAI API Key ###

# Display the API key in a text input field
new_api_key = st.text_input("API Key", value=api_key, help="You can find your API key at https://platform.openai.com/api-keys.")

# If the API key is modified and not empty, update it
if new_api_key != api_key and new_api_key.strip() != "":

    # Update the API key
    secrets["api_keys"]["openai"] = new_api_key

    # Write back to file
    with open(secrets_path, "w") as f:
        toml.dump(secrets, f)

    # Rerun to apply changes
    st.rerun()


### Local Mode ###
ollama_flag = secrets.get("settings", {}).get("ollama_flag", 0)

def update_flag(value):
    # Update both the secrets dict and st.secrets
    secrets["settings"] = secrets.get("settings", {})
    secrets["settings"]["ollama_flag"] = value
    with open(secrets_path, "w") as f:
        toml.dump(secrets, f)
    # st.rerun()

# Simplify the toggle logic
local_mode = st.toggle(
    "Local Mode",
    value=bool(ollama_flag),
    key="local_mode",
    on_change=update_flag,
    args=(1 if not ollama_flag else 0,),
    help="Toggle local mode and run models locally for 100% free usage. No OpenAI API key required. See the FAQ for more information."
)


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