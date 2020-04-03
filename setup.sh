apt-get install python3-venv
python3 -m venv py_env
chmod +x py_env/bin/activate
./py_env/bin/activate
pip3 install -r requirements.txt
pip3 install -e device_manager/
pip3 install -e procedure_manager/

