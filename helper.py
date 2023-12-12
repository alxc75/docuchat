# This file is a collection of helper functions for the Docuchat Streamlit app that shouldn't be written elsewhere.
# Import this file as a module to use the functions.

import os
import json

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