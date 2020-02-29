from flask import Flask, request, Response
import procedure_manager as pm
from procedure_manager.procedure_reader import Proc_Reader
from device_manager.coms_manager import COM_Manager

from pprint import pprint as pp
import json

app = Flask(__name__)

@app.route('/tests')
def get_tests():
    return get_test_list()

@app.route('/get_readings')
def get_readings():
    reading = COM_Manager().get_readings()
    print(f'Reading: {str(reading)}')
    return Response(str(reading), mimetype='application/json')

@app.route('/pneumatic_ctrl', methods=['POST'])
def pneumatic_ctrl():
    COM_Manager().send_pneu_ctrl(request.values['signal'])
    return Response(request.values['signal'], mimetype='text/xml')

@app.route('/start_test')
def start_test():
    procedure = Proc_Reader("test_schema.xsd", "output.xml")
    return Response()

@app.route('/load_procedure')
def load_procedure():
    Proc_Reader("test_schema.xsd", "output.xml")
    Proc_Reader().get_dict_proc()
    return Response(str(cur_procedure), mimetype='text/xml')

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

@app.route('/adjust_control')
def adjust_control():
    pass

@app.route('/label_device')
def label_device():
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
    app.run()

# if __name__ == '__main__':
#     reset_device_comms()