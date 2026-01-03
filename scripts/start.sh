#!/bin/bash
ENV_NAME=$(pwd | awk '{split($0,a,"/"); print "env_"a[length(a)-1]}')
PYTHON_PATH=$(ls /c/Users/*/AppData/Local/Programs/Python/Python*/python.exe | tail -1)
echo "Using virtual environment: $ENV_NAME"
echo "Using Python path: $PYTHON_PATH"
# ls "$ENV_NAME/Scripts/activate"
if [[ -d "$ENV_NAME" ]]; then

    source "$ENV_NAME/Scripts/activate"
    cd ..
    streamlit run ./projeto_metricas_whatsapp.py > log_application.log 

else
    echo "Virtual environment $ENV_NAME does not exist. Please create it first."
fi
