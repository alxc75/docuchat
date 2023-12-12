import streamlit as st
import os
import sys
import time
import subprocess

def platform():
    if sys.platform == "win32":
        return "Windows"
    elif sys.platform == "darwin":
        return "MacOS"
    elif sys.platform == "linux":
        return "Linux"
    else:
        return "Unknown"

st.title("Local Mode")
st.subheader("Instructions to run a local model on you computer.")
time.sleep(1)
st.write("Attempting OS detection...")
time.sleep(1)
st.write(f"Detected platform: {platform()}")
time.sleep(1)

def install():
    if sys.platform == "darwin":
        # Check for 'make' on macOS
        try:
            subprocess.call("git")
            st.write("Git is found, proceeding...")
            time.sleep(1)
            st.write("A pop-up may appear to install Xcode Command Line Tools. Please click the Reload button below"
                     " once the installation is complete.")
            repo = "https://github.com/ggerganov/llama.cpp.git"
            path = os.path.dirname(os.path.realpath(__file__))
            time.sleep(1)
            st.write(f"Working directory: {path}")
            time.sleep(1)
            st.write("Cloning llama.cpp")
            subprocess.run(f"git clone {repo} {path}/llama.cpp", shell=True)
            time.sleep(2)
            st.write("Done, building for macos...")
            subprocess.run(f"cd {path}/llama.cpp", shell=True)
            time.sleep(2)
            cpp_dir = f"{path}/llama.cpp"
            subprocess.run("/usr/bin/make", shell=True, cwd=cpp_dir)
            st.write("Installation complete!")
            time.sleep(1)
            st.write("Installing server requirements...")
            subprocess.run("pip3 install -r requirements.txt", shell=True, cwd=cpp_dir)
            st.write("Done. Launching server...")
            subprocess.run("./server -m models/stablelm-zephyr-3b.Q3_K_S.gguf -c 2048", shell=True, cwd=cpp_dir)
            # At this point the server should have launched.
            # to-do: finally fix this issue with working directory to download all to the right place.

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


llama_path =  os.path.dirname(os.path.realpath(__file__)) + "/llama.cpp"
if os.path.exists(llama_path):
    st.write("Existing installation found.")
else:
    st.write("No existing installation found. Please install the required dependencies with the button below or manually.")
st.button("Install", on_click=install)