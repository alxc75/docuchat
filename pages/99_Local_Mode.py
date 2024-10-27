import huggingface_hub
import streamlit as st
import os
import sys
import time
import subprocess
import threading
import json
import platform

st.title("Local Mode")
st.subheader("Instructions to run a local model on you computer.")

current_path =  os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.dirname(current_path)
llama_path = parent_path + "/llama.cpp"
#st.write(f"Looking in {llama_path}") # Show the llama.cpp path
server_path = llama_path + "/server"
model_path = llama_path + "/models"

# Read the existing data from the userinfo.json file
with open("userinfo.json", "r") as f:
    userinfo = json.load(f)

# Check if the server_path exists
if os.path.exists(server_path):
    install_flag = 1
    # Count and fetch installed models
    filtered = [file for file in os.listdir(model_path) if not file.startswith("ggml") and not file.startswith(".")]
    num_filtered = len(filtered)
else:
    install_flag = 0

# Update the value of the install_flag key in the loaded data
userinfo["install_flag"] = install_flag

# Write the updated data back to the file
with open("userinfo.json", "w") as f:
    json.dump(userinfo, f, indent=4)

# Create session variable for the persistent stop server button
if "server_running" not in st.session_state:
    st.session_state.server_running = False

def get_platform():
    if sys.platform == "win32":
        return "Windows"
    elif sys.platform == "darwin":
        return "MacOS"
    elif sys.platform == "linux":
        return "Linux"
    else:
        return "Unknown"


def install():
    time.sleep(0.5)
    st.write("Attempting OS detection...")
    time.sleep(0.5)
    if get_platform() != "Unknown":
        st.write(f"Detected platform: {get_platform()}")
    else:
        st.write("Your platform couldn't be automatically detected. Please follow the manual instructions below.")
    time.sleep(0.5)

    if sys.platform == "darwin":
        llama_path = parent_path + "/llama.cpp"
        # Check for 'make' on macOS
        try:
            subprocess.call("git")
            st.write("Git is found, proceeding...")
            time.sleep(1)
            st.write("A pop-up may appear to install Xcode Command Line Tools. Please click the Reload button below"
                     " once the installation is complete.")
            repo = "https://github.com/ggerganov/llama.cpp.git"
            time.sleep(1)
            st.write(f"Cloning llama.cpp into {llama_path}")
            subprocess.run(f"git clone {repo} {parent_path}/llama.cpp", shell=True)
            time.sleep(2)
            st.write("Done, building for macOS...")
            time.sleep(2)
            subprocess.run("/usr/bin/make", shell=True, cwd=llama_path)
            st.write("Installation complete!")
            time.sleep(1)
            st.write("Installing server requirements...")
            subprocess.run("pip3 install -r requirements.txt", shell=True, cwd=parent_path)
            time.sleep(1)
            st.write("Downloading default model...")
            subprocess.run("huggingface-cli download TheBloke/dolphin-2.6-mistral-7B-GGUF dolphin-2.6-mistral-7b.Q4_K_M.gguf --local-dir . --local-dir-use-symlinks False", shell=True, cwd=model_path)
            st.markdown("""
            Installation complete!\n
            You can now start the local server by clicking the button below.
            """)

        except subprocess.CalledProcessError:
            st.write("Sorry, an error occurred. Please check the manual installation instructions below.")

    elif sys.platform == "win32":
        # Check for 'cmake' on Windows. It would be nice to eventually switch to an automated install here as well: https://silentinstallhq.com/cmake-silent-install-how-to-guide
        try:
            llama_path = parent_path + "\llama.cpp"
            subprocess.check_output(["where", "cmake"])
            st.write("Cmake is installed, proceeding...")
            subprocess.call('git', shell=False)
            st.write("Git is found, proceeding...")
            time.sleep(1)
            repo = "https://github.com/ggerganov/llama.cpp.git"
            time.sleep(1)
            st.write(f"Cloning llama.cpp into {llama_path}")
            subprocess.run(f"git clone {repo} {parent_path}/llama.cpp", shell=True)
            time.sleep(2)
            st.write("Done, building for Windows...")
            time.sleep(2)
            subprocess.run("rm CMakeCache.txt", cwd=llama_path)
            subprocess.run("cmake .", cwd=llama_path)
            subprocess.run("mkdir build", cwd=llama_path)
            build_dir = parent_path + r'\llama.cpp\build'
            #subprocess.run("cmake ..", cwd=build_dir)
            st.write(f"Building into {build_dir}")
            subprocess.run(f"cmake --build {build_dir} --config Release", cwd=llama_path)


        except subprocess.CalledProcessError:
            st.write("cmake is not installed. Please install it from https://cmake.org/download/ (you want the x64 installer in the Binary Distributions). Make sure you add Cmake to your system path when the installer prompts you and click the "
                     "Reload button below. Also please check you have `git` on your system.")
            st.button("Reload")

    elif sys.platform == "linux":
        st.write("Sorry, Linux distributions don't have an autoinstaller (yet). Please follow the manual installation instructions below.")
    else:
        st.write("Unsupported platform, please check the manual installation instructions below.")




# Global variable to hold the subprocess
proc = None

def start_server():
    global proc
    if install_flag == 1:
        st.write(model_path)
        if num_filtered == 0:
            st.write("No model found!")
        else:
            st.write("Starting server. Use the button below to stop it.")
            # Start the subprocess in a new thread
            proc = subprocess.Popen(["./server", "-m", f"{model_path}/{model}", "-c", "7892"], shell=False, cwd=llama_path)
            if "process" not in st.session_state:
                st.session_state.process = proc
            # Wait for the process to complete
            proc.wait()

def stop_server():
    if "process" not in st.session_state:
        global proc
    else:
        proc = st.session_state.process
    st.write(f"Found process: {proc}")
    if proc:
        st.toast("Local server stopped!")
        # Terminate the subprocess
        proc.terminate()
        proc = None
        # Remove the persistent stop button
        st.session_state.server_running = False

# Streamlit UI
def start():
    if install_flag == 1:
        st.write(model_path)
        if num_filtered == 0:
            st.write("No model found!")
        else:
            st.write("Starting server. Use the button below to stop it.")

            # Stop button
            st.button("Stop Local Server", key="server_stop", on_click=stop_server)

# Note, the context window here is 8092 minus an approximate answer length of 200 tokens, hence 7892.
# Will have to be changed according to the model chosen.


def download_model():
    st.write("Downloading model, please wait...")
    #subprocess.run("huggingface-cli download TheBloke/stablelm-zephyr-3b-GGUF stablelm-zephyr-3b.Q3_K_S.gguf --local-dir . --local-dir-use-symlinks False", shell=True, cwd=model_path)    # Old model for testing, doesn't use the ChatML prompt format
    huggingface_hub.hf_hub_download(repo_id="TheBloke/dolphin-2.6-mistral-7B-GGUF", filename="dolphin-2.6-mistral-7b.Q4_K_M.gguf", local_dir=model_path, local_dir_use_symlinks=False)
    st.write("Done!")


if install_flag == 1 and num_filtered > 0:
    st.write("Existing installation found.")
    with st.expander("Installed models", expanded=False):
        st.write(f"Found {num_filtered} model(s):")
        for file in filtered:
            st.write(file)
    model = st.selectbox("Select a model", filtered)
    # Start thread button
    if st.button("Start Local Server"):
        # Start the server in a separate thread
        server_thread = threading.Thread(target=start_server)
        server_thread.start()
        st.toast("Local server started!")
        # Add persistent stop button
        if "server_running" not in st.session_state:
            st.session_state.server_running = True
        else:
            st.session_state.server_running = True
        #st.button("Stop Local Server", key="server_stop", on_click=stop_server)
elif install_flag == 1 and num_filtered == 0:
    st.write("No model found! Please install a model first with the button below or manually.")
    st.button("Download model", on_click=download_model)
    st.markdown("Want more models? Get them [here](https://huggingface.co/TheBloke). Make sure they use the ChatML prompt format and are in the .gguf format.")
else:
    st.write("No existing installation found. Please install the required dependencies with the button below or manually.")
    st.button("Install", on_click=install)

if get_platform() == "Windows":
    st.info("Make sure Cmake is installed! Download it from https://cmake.org/download/ (you want the x64 installer in the Binary Distributions). Don't forget to add Cmake to your system path when the installer prompts you. ")
if "ARM" in platform.machine() or "ARM" in platform.processor():
    st.error("Sorry, the auto-installer doesn't work on Windows ARM64 platforms. Please refer to the manual installation instructions below.")

if st.session_state.server_running:
    st.button("Stop Local Server", key="server_stop", on_click=stop_server)


# Manual installation instructions
with st.expander("Manual Installation Instructions", expanded=False):
    st.markdown("""
    ## Manual Installation Instructions
    If the automatic installation failed or your system is not supported, you can follow these instructions to install the required dependencies manually.

    - **Step 1:** Install make (macOS and Linux) or [cmake](https://cmake.org/download/) (Windows) and git. You should already have the latter unless you've downloaded DocuChat as a ZIP file.
    - **Step 2:** Clone the llama.cpp repository from [GitHub](https://github.com/ggerganov/llama.cpp.git) into the root of the DocuChat folder:
    ```bash
    git clone https://github.com/ggerganov/llama.cpp.git
    ```
    - **Step 3:** Compile the repo. This may take a while depending on your computer. Get the instruction for your platform [here](https://github.com/ggerganov/llama.cpp?tab=readme-ov-file#build).
    - **Step 4:** Install the Python requirements. You can do this by running the following command still in the root of the DocuChat folder:
    ```bash
    pip3 install -r requirements.txt
    ```
    - **Step 5:** Download a model. You can do this by clicking the button below or by downloading them [here](https://huggingface.co/TheBloke). Make sure they use the **ChatML** prompt format (Dolphin, OpenOrca, OpenHermes, OpenChat-3.5, etc.) and are in the **.gguf** format.
    """)

    st.button("Download model", on_click=download_model)


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