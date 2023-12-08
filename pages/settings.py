import streamlit as st
import json
import os

st.sidebar.title("Settings")
st.sidebar.markdown("Use this tab to change your OpenAI API key.")
st.title("Settings")
st.markdown("Please enter your OpenAI API key below.")

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

# Display the API key in a text input field
new_api_key = st.text_input("API Key", value=api_key, help="You can find your API key at https://platform.openai.com/api-keys.")

# If the API key is modified and not empty, update it
if new_api_key != api_key and new_api_key.strip() != "":
    userinfo["api_key"] = new_api_key
    with open("userinfo.json", "w") as f:
        json.dump(userinfo, f, indent=4)
    st.experimental_rerun()  # Force a rerun to reload the updated userinfo.json