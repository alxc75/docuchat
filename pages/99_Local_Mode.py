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

def check_make_or_cmake():
    if sys.platform == "darwin":
        # Check for 'make' on macOS
        try:
            subprocess.check_output(["which", "make"])
            st.write("make is installed. Proceeding...")
        except subprocess.CalledProcessError:
            st.write("make is not installed. Asking for permission.")
            st.write("A pop-up will appear to install Xcode Command Line Tools. Please click the Reload button below"
                     " once the installation is complete.")
            st.button("Reload", on_click=st.rerun())
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

check_make_or_cmake()

