# This file is a collection of helper functions for the Docuchat Streamlit app that shouldn't be written elsewhere.
# Import this file as a module to use the functions.

import os
import json


import os
import toml
import streamlit as st

def secretmaker():
    """Create and manage Streamlit secrets for API keys and endpoints"""

    # Define default values
    default_secrets = {
        "api_keys": {
            "openai": "",
        },

        "ollama": {
            "endpoint": "http://localhost:11434",
            "ollama_flag": 0,
            "default_model": ""
        }
    }

    # Ensure .streamlit directory exists
    os.makedirs(".streamlit", exist_ok=True)
    secrets_path = ".streamlit/secrets.toml"

    # Create secrets.toml if it doesn't exist
    if not os.path.exists(secrets_path):
        with open(secrets_path, "w") as f:
            toml.dump(default_secrets, f)
        st.warning("Created new secrets file at .streamlit/secrets.toml")

    # Load existing secrets or use defaults
    try:
        # Get values from st.secrets with fallbacks to defaults
        api_key = st.secrets.api_keys.get("openai", default_secrets["api_keys"]["openai"])
        ollama_flag = st.secrets.ollama.get("ollama_flag", default_secrets["ollama"]["ollama_flag"])

    except Exception as e:
        st.error(f"Error loading secrets: {str(e)}")
        api_key = default_secrets["api_keys"]["openai"]
        ollama_flag = default_secrets["ollama"]["ollama_flag"]

    return api_key, ollama_flag

# Get the secrets for use in other files
api_key, ollama_flag = secretmaker()

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
