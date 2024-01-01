# This file is a collection of helper functions for the Docuchat Streamlit app that shouldn't be written elsewhere.
# Import this file as a module to use the functions.

import os
import json


def jsonmaker():
    # Set default values for variables
    api_key = ""
    endpoint = "https://api.openai.com/v1/"
    install_flag = 0
    # Check whether the userinfo.json file exists
    if os.path.exists("userinfo.json"):
        # Check whether the API key is set
        with open("userinfo.json", "r") as f:
            userinfo = json.load(f)
            if "api_key" in userinfo:
                api_key = userinfo["api_key"]
                endpoint = "https://api.openai.com/v1/"
                if "install_flag" not in userinfo:
                    install_flag = 0
            else:
                api_key = ""
                endpoint = "http://localhost:8080/v1"
                if "install_flag" not in userinfo:
                    install_flag = 0


    # If the userinfo.json file does not exist, create it
    else:
        api_key = ""
        endpoint = "https://api.openai.com/v1/"
        install_flag = 0

        userinfo = {
            "api_key": api_key,
            "endpoint": endpoint,
            "install_flag": install_flag
        }
        with open("userinfo.json", "w") as f:
            json.dump(userinfo, f, indent=4)


    return api_key, endpoint, install_flag


api_key, endpoint, install_flag = jsonmaker()    # Calling for the other files accessing the variables in this file.

# ------------------- LICENSE -------------------
# Docuchat, a smart knowledge assistant for your documents.
# Copyright © 2024 xTellarin
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
