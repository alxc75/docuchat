import streamlit as st
import json
import os

# Somehow prevents a streamlit bug with set_page_config warning appearing for no reason.
def main():
    print("Launching Settings")
try:
    main()
except Exception as e:
    print("An error has occurred: ", e)

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
    st.rerun()  # Force a rerun to reload the updated userinfo.json

if __name__ == "__main__":
    main()

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