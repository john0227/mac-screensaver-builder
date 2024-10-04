#!/bin/bash

# Quit script on error
set -e

brew_install_pythontk() {
    # Check if brew exists in user system
    if ! command -v brew &> /dev/null
    then
        echo "Command 'brew' not found"
        echo "Go to https://brew.sh/ to install 'brew'"
        exit 1
    fi

    # Ask user if they want to install python-tk with brew
    read -r -p "Run 'brew install python-tk'? (y/n): " response
    if [[ $response =~ ^([yY][eE][sS]|[yY])$ ]]
    then
        brew install python-tk
        exit 0
    else
        echo "Install python-tk in order to run screensaver builder"
        exit 1
    fi
}

# Check if python-tk is installed
python -c "import tkinter" > /dev/null 2> /dev/null || \
if [ $? -ne 0 ]
then
    brew_install_pythontk
fi

# Check if virtual environment is set up
if [ ! -d "venv" ]
then
    python -m venv venv
fi
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt > /dev/null

# Run the program
python build_screensaver.py
