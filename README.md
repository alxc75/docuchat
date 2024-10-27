# DocuChat

DocuChat is a locally-hosted application to summarize and chat with your documents. Use the OpenAI API or run models locally for 100% free usage. You can even query multiple documents thanks to state-of-the-art RAG integrations.

![Python Version](https://img.shields.io/badge/Python-3.11-blue?logo=python)

## Features

- **Intuitive, no-code UI**: enter your OpenAI API key in the Settings and you're ready to go.
- **Simple or Interactive Mode:** get a quick summary or ask complex questions about your document.
- **Model flexibility:** use OpenAI's latest model for cheap and fast results, or run a model locally for free. [In Progress]
- **Advanced Features:** toggle advanced mode to upload and query multiple documents at once, with citations. [In Progress]

## Installation
Clone the repository somewhere on your computer. You may have to install `git` first.
```bash
git clone https://github.com/xTellarin/docuchat.git
```
### Using Anaconda (Recommended)
If you don't have Anaconda installed, grab it [here](https://www.anaconda.com/products/individual).

Next, move into the DocuChat folder to create a new environment and install the dependencies:
```bash
conda create -n docuchat python=3.11
```
```bash
conda activate docuchat
```
```bash
cd docuchat && pip install -r requirements.txt
```

### Using Pip
```bash
pip install -r requirements.txt
```

## Usage
All you need to do to use DocuChat is run the following terminal command in your DocuChat folder:
```bash
streamlit run main.py
```
Your browser will automatically open DocuChat at http://localhost:8501/.
You'll need to get your OpenAI API key (get it [here](https://platform.openai.com/account/api-keys)) and enter it into the Settings tab. Alternatively, you can run models locally for free (coming soon!).

# FAQ
**Q: [Windows] I'm getting an `streamlit : The term 'streamlit' is not recognized as the name of a cmdlet` error when I try to run DocuChat**

A: You can either run `python -m streamlit run main.py` or [add Python to your PATH](https://datatofish.com/add-python-to-windows-path/).
The latter is recommended if you plan on using Python in the future.
Then open a new terminal window and run `pip install streamlit` to install Streamlit globally. Now you can run DocuChat with `streamlit run main.py`.

###
**Q: I'm getting a `ModuleNotFoundError: No module named _xxx_` error when I try to run DocuChat**

A: Open a new terminal window and run `pip install -r requirements.txt` to install the missing dependencies, then try running DocuChat again. Shouldn't happen but Python is weird sometimes.

###
**Q: Can I download any model for local use?**

A: As long as your model uses the ChatML instruction template, yes. You can find models on the [HuggingFace Hub](https://huggingface.co/models?pipeline_tag=text-generation&sort=trending).
## Contributing
DocuChat is still in active development and you are very welcome to contribute to its development! To get started, fork the repo, make your changes and submit a pull request.

You can also open an issue if you find a bug or have a feature request.

Thank you for using DocuChat!