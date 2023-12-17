import huggingface_hub
import streamlit as st
import os
import sys
import time
import subprocess

st.title("Local Mode")
st.subheader("Instructions to run a local model on you computer.")

current_path =  os.path.dirname(os.path.realpath(__file__))
parent_path = os.path.dirname(current_path)
llama_path = parent_path + "/llama.cpp"
#st.write(f"Looking in {llama_path}") # Show the llama.cpp path
server_path = llama_path + "/server"
model_path = llama_path + "/models"

install_flag, filtered, num_filtered = None, None, None
if os.path.exists(server_path):
    install_flag = 1
    # Count and fetch installed models
    filtered = [file for file in os.listdir(model_path) if not file.startswith("ggml") and not file.startswith(".")]
    num_filtered = len(filtered)

else:
    install_flag = 0


def platform():
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
    if platform() != "Unknown":
        st.write(f"Detected platform: {platform()}")
    else:
        st.write("Your platform couldn't be automatically detected. Please follow the manual instructions below.")
    time.sleep(0.5)

    if sys.platform == "darwin":
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
            subprocess.run("huggingface-cli download TheBloke/stablelm-zephyr-3b-GGUF stablelm-zephyr-3b.Q3_K_S.gguf --local-dir . --local-dir-use-symlinks False", shell=True, cwd=model_path)
            st.markdown("""
            Installation complete!\n
            You can now start the local server by clicking the button below.
            """)

        except subprocess.CalledProcessError:
            st.write("Sorry, an error occurred. Please check the manual installation instructions below.")

    elif sys.platform == "win32":
        # Check for 'cmake' on Windows
        try:
            subprocess.check_output(["where", "cmake"])
            st.write("cmake is installed, proceeding...")
        except subprocess.CalledProcessError:
            st.write("cmake is not installed. Please install it from https://cmake.org/download/ and click the "
                     "Reload button below.")
            st.button("Reload", on_click=st.rerun())
    else:
        st.write("Unsupported platform, please check the manual installation instructions below.")




def start():
    if install_flag == 1:
        st.write(model_path)
        if num_filtered == 0:
            st.write("No model found!")
        else:
            st.write("Starting server. Use the button below to stop it.")
            st.button("Stop Local Server", on_click=st.stop)
            subprocess.run(["./server", "-m", f"{model_path}/{model}", "-c", "7892"], shell=False, cwd=llama_path)
# Note, the context window here is 8092 minus an approximate answer length of 200 tokens, hence 7892.
# Will have to be changed according to the model chosen. Try to add a dropdown in the settings tab with
# common model values. Or use a dropdown for other common models to download instead.


def download_model():
    st.write("Downloading model, please wait...")
    #subprocess.run("huggingface-cli download TheBloke/stablelm-zephyr-3b-GGUF stablelm-zephyr-3b.Q3_K_S.gguf --local-dir . --local-dir-use-symlinks False", shell=True, cwd=model_path)
    huggingface_hub.hf_hub_download(repo_id="TheBloke/stablelm-zephyr-3b-GGUF", filename="stablelm-zephyr-3b.Q4_K_M.gguf", local_dir=model_path, local_dir_use_symlinks=False)
    st.write("Done!")


if install_flag == 1 and num_filtered > 0:
    st.write("Existing installation found.")
    with st.expander("Installed models", expanded=False):
        st.write(f"Found {num_filtered} model(s):")
        for file in filtered:
            st.write(file)
    model = st.selectbox("Select a model", filtered)
    st.button("Start Local Server", on_click=start)
elif install_flag == 1 and num_filtered == 0:
    st.write("No model found! Please install a model first with the button below or manually.")
    st.button("Download model", on_click=download_model)
    st.markdown("Want more models? Get them [here](https://huggingface.co/TheBloke).")
else:
    st.write("No existing installation found. Please install the required dependencies with the button below or manually.")
    st.button("Install", on_click=install)

