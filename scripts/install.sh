#!/bin/bash
ENV_NAME=$(pwd | awk '{split($0,a,"/"); print "env_"a[length(a)-1]}')
PYTHON_PATH=$(ls /c/Users/*/AppData/Local/Programs/Python/Python*/python.exe | head -1)
if [[ -z "$PYTHON_PATH" ]]; then
    echo "Python installation not found. Please install Python first."
    exit 1
fi
if [[ ! -d "$ENV_NAME" ]]; then
    echo "Creating virtual environment..."
    $PYTHON_PATH -m venv "$ENV_NAME"
    echo "Virtual environment created."
    echo "Activating virtual environment..."
    source "$ENV_NAME/Scripts/activate"
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip freeze > installed_packages.txt
    echo "All dependencies installed."
else
    echo "Virtual environment already exists."
fi
