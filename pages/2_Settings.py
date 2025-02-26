import streamlit as st
import json
import os
from helper import api_key

st.sidebar.title("Settings")
st.sidebar.markdown("Use this tab to change your OpenAI API key.")
st.title("Settings")
st.markdown("Please enter your OpenAI API key below.")

# Duplicated from helper.py, shouldn't be necessary.
# Check whether the userinfo.json file exists
if os.path.exists("userinfo.json"):
    # Check whether the API key is set
    with open("userinfo.json", "r") as f:
        userinfo = json.load(f)
        if "api_key" in userinfo:
            api_key = userinfo["api_key"]
        else:
            api_key = ""

# # If the userinfo.json file does not exist, create it
if not os.path.exists("userinfo.json"):
    with open("userinfo.json", "w") as f:
        userinfo = {}
        api_key = ""
        json.dump(userinfo, f, indent=4)

# Display the API key in a text input field
new_api_key = st.text_input("API Key", value=api_key, help="You can find your API key at https://platform.openai.com/api-keys.")

# If the API key is modified and not empty, update it
if new_api_key != api_key and new_api_key.strip() != "":
    userinfo["api_key"] = new_api_key
    with open("userinfo.json", "w") as f:
        json.dump(userinfo, f, indent=4)
    st.rerun()  # Force a rerun to reload the updated userinfo.json


# Toggle local mode
with open("userinfo.json", "r") as f:
    userinfo = json.load(f)
if "ollama_flag" in userinfo:
    ollama_flag = userinfo["ollama_flag"]
else:
    ollama_flag = 0    # Because if the key doesn't exist, it's logically not installed. Shouldn't be invoked normally anyway.

if ollama_flag == 1:
    local_mode = st.empty()
    if userinfo.get("endpoint") == "http://localhost:8080/v1":  # Using the get() method to avoid a KeyError if endpoint doesn't exist
        local_mode = st.toggle("Local Mode", value=True, key="local_mode", help="Toggle local mode and run models locally for "
                                                                    "100% free usage. No OpenAI API key required. "
                                                                    "See the FAQ for more information.")
    else:
        local_mode = st.toggle("Local Mode", value=False, key="local_mode", help="Toggle local mode and run models locally for "
                                                                    "100% free usage. No OpenAI API key required. "
                                                                    "See the FAQ for more information.")
    # Read the existing data from the userinfo.json file
    with open("userinfo.json", "r") as f:
        userinfo = json.load(f)

    # Update the value of the endpoint key based on the local_mode value
    if local_mode:
        userinfo["endpoint"] = "http://localhost:8080/v1"
    else:
        userinfo["endpoint"] = "https://api.openai.com/v1/"

    # Write the updated data back to the file
    with open("userinfo.json", "w") as f:
        json.dump(userinfo, f, indent=4)
else:
    local_mode = st.toggle("Local Mode", disabled=True, value=False, key="local_mode", help="Visit the Local Mode tab to install the local requirements.")


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