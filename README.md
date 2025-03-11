# DocuChat

DocuChat is a locally-hosted application to summarize and chat with your documents. Use the OpenAI API or run models locally with Ollama for 100% free usage. You can even query multiple documents thanks to state-of-the-art RAG integrations.

![Python Version](https://img.shields.io/badge/Python-3.11-blue?logo=python)

### **NOTE: a hosted version of DocuChat is coming soon™**

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
streamlit run Home.py
```
Your browser will automatically open DocuChat at http://localhost:8501/.
You'll need to either get your OpenAI API key (get it [here](https://platform.openai.com/account/api-keys)) and enter it into the Settings tab or install [Ollama](https://ollama.com/) if you want to run models locally.

# FAQ
**Q: [Windows] I'm getting a `streamlit : The term 'streamlit' is not recognized as the name of a cmdlet` error when I try to run DocuChat**

A: You can either run `python -m streamlit run main.py` or [add Python to your PATH](https://datatofish.com/add-python-to-windows-path/).
The latter is recommended if you plan on using Python in the future.
Then open a new terminal window and run `pip install streamlit` to install Streamlit globally. Now you can run DocuChat with `streamlit run main.py`.

###
**Q: I'm getting a `ModuleNotFoundError: No module named _xxx_` error when I try to run DocuChat**

A: Open a new terminal window and run `pip install -r requirements.txt` to install the missing dependencies, then try running DocuChat again. Shouldn't happen but Python is weird sometimes.

###
**Q: Can I download any model for local use?**

A: Of course. If you don't know which one to choose, DocuChat will recommend one. Otherwise, you can use the Ollama `pull` command followed by the model name. Find a model [here](https://ollama.com/search).

###
**Q: I am getting a *LookupError: XXX not found*. What do I do?**

A: You need to install some NLTK models. In a terminal window with the docuchat environment active, open the Python interpreter with `python` and use the following two commands:

```bash
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
```

## Roadmap
- [x] Collection management
- [x] Local Mode (with Ollama)
- [ ] Cloud-based embedding
- [ ] OpenRouter support for free API models

## Contributing
DocuChat is still in active development and you are very welcome to contribute to its development! To get started, fork the repo, make your changes and submit a pull request.

You can also open an issue if you find a bug or have a feature request.

Thank you for using DocuChat!
