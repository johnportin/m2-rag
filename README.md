# m2-rag
A RAG-based chatbot for interacting with the M2 language.

## Setup

Create a virtual environment. I choose to use pipenv for managing my environments, and pyenv for managing my versions of python.

To set your version of python. I happen to have built this project on version 3.13.4, but any modern version will likely work. 

    ```bash
    pyenv install 3.13.4  # or whatever version the project uses
    pyenv local 3.13.4
    ```

To create the environment, simply use:

    ```bash
    pipenv install
    ```

You can either set your IDE's interpreter to this environment, or activate it in a shell with

    ```bash
    pipenv shell
    ```

## Running the project

This section contains the details needed to run the project from scratch

### Downloading data

Run the `get_data.py` script to download the documents from the M2 github repository.

    ```bash
    python src/scripts/get_data.py
    ```

### Parsing data

The data comes in raw `.m2` files, a format which is not often worked with outisde of the small world of commutative algebra research. Thus we have a custom parser for these documents. To parse all files, run:

    ```bash
    python src/scripts/run_parser.py
    ```