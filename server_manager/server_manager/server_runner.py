from flask import Flask, request, Response, session
import procedure_manager as pm
from procedure_manager.procedure_reader import Proc_Reader
from device_manager.coms_manager import COM_Manager

from functools import wraps
from pprint import pprint as pp
import json

app = Flask(__name__)

def validate_json_for(*required_fields):
    def validated_endpoint(endpoint_func):
        @wraps(endpoint_func)
        def validation_wrapper(*args, **kwargs):
            data = request.get_json(silent=True)
            if data is None:
                return Response(f"Request must include json with keys: {required_fields}", status=400, mimetype='text/xml')

            field_diff = set(required_fields).difference(set(data.keys()))
            if field_diff:
                return Response(f"Missing fields in json payload: {field_diff}", status=400, mimetype='text/xml')

            return endpoint_func(*args, **kwargs)
        return validation_wrapper
    return validated_endpoint

@app.route('/label_device', methods=['POST'])
@validate_json_for('device_label')
def label_device():
    data = request.get_json()
    dev_label = data['device_label']

    dev_uuid = data.get('device_id')
    if dev_uuid:
        COM_Manager().set_device_label(dev_uuid, dev_label)
        return Response(f"Set the device label for {dev_uuid} to {dev_label}", mimetype="text/xml")

    dev_label_id = data.get('old_label')
    if dev_label_id:
        if COM_Manager().update_device_label(dev_label_id, dev_label):
            return Response(f"Set the device label for {dev_label_id} to {dev_label}", mimetype="text/xml")
        else:
            return Response(f"The label provided was not found", mimetype="text/xml")

    return Response("Require either device_id or old_label headers", 400, mimetype="text/xml")

@app.route('/clear_device_label', methods=['POST'])
@validate_json_for('device_label')
def clear_device_label():
    device_label = request.get_json()['device_label']
    COM_Manager().clear_device_label(device_label)

    return Response(f"Label '{device_label}' removed", mimetype="text/xml")

@app.route('/tests')
def get_tests():
    return get_test_list()

@app.route('/get_readings')
def get_readings():
    reading = COM_Manager().get_readings()
    print(f'Reading: {str(reading)}')
    return Response(str(reading), mimetype='application/json')

@app.route('/pneumatic_ctrl', methods=['POST'])
@validate_json_for('signal')
def pneumatic_ctrl():
    signal = request.get_json()['signal']
    COM_Manager().send_pneu_ctrl(signal)
    return Response(f"Signal {signal} sent", mimetype='text/xml')

@app.route('/active_user', methods=['GET', 'POST'])
def active_user():
    data = request.get_json()
    if request.method == 'POST':
        if 'user' not in data:
            return Response("POST request must include the 'user' header", 400, mimetype='text/xml')
        user = data['user']
        session['user'] = user
        return Response(f"Active user set to {user}", mimetype='text/xml')

    if 'user' not in session:
        return Response("No active user", mimetype='text/xml')
    return Response(session['user'], mimetype='text/xml')

@app.route('/start_test')
def start_test():
    procedure = Proc_Reader("test_schema.xsd", "output.xml")
    return Response()

@app.route('/load_procedure')
def load_procedure():
    Proc_Reader("test_schema.xsd", "output.xml")
    Proc_Reader().get_dict_proc()
    r = str(Proc_Reader())
    return Response(r, mimetype='text/xml')

@app.route('/next_step')
def next_step():
    return Response(json.dumps(Proc_Reader().get_step()), mimetype='json')

@app.route('/stop_test')
def stop_test():
    procedure_runner.stop_test()

@app.route('/delete_test_run')
def delete_test_run():
    pass

@app.route('/perform_step')
def perform_step():
    pass

@app.route('/look_for_devices')
def look_for_devices():
    pass

@app.route('/register_device')
def register_device():
    pass

@app.route('/ping_device')
def ping_device():
    pass

@app.route('/reset')
def reset_device_comms():
    pass

if __name__ == '__main__':
    COM_Manager()
    app.config.update(
        SECRET_KEY='via_fydp_ak8w?hi-95'
    )
    app.run()
