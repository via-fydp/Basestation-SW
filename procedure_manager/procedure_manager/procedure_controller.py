from ast import literal_eval
from dataclasses import dataclass
import logging
from math import isclose
import os
import yaml

from lxml import etree

from .procedure_utils import verify_with_schema
from .procedure_builder import Procedure
from .procedure_reader import Proc_Reader

def make_logger():
    logger = logging.getLogger('control_logger')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('controller.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

def init_action_functions():
    action_functions = {
        'check': {
            'pressure_sensor': check_pressure_sensor,
            'user_validate': check_user_validate
        }
    }

@dataclass
class Step_Result:
    """ Class to keep track of step results """
    passed: bool
    actions_taken: list

@dataclass
class Action_Result:
    """ Class to keep track of test step results """
    error: bool
    result_tip: str
    result_value: str
    action_taken: str = None
    transmit: bool = False
    step_id: str = None

class Proc_Controller():

    def __init__(self, proc_dir, control_unit_com, device_manager):
        self.logger = logging.getLogger('control_logger')
        self._base_proc_dir = proc_dir
        self._proc_reader = None
        if not os.path.exists(self._base_proc_dir):
            os.makedirs(self._base_proc_dir)

        self.controller_com = control_unit_com
        self.device_manager = device_manager
        self.start_comms(control_unit_com, sensor_com)

    def start_comms(self, control_unit_com):
        pass

    def get_procs(self):
        """ Returns a list of procedures by reading the process directory """
        pass

    def make_proc(self, proc):
        """ Makes the relevant directory for a test procedure, writes the metadata and procedure
        file to the location

        Args:
            proc: a procedure_builder.Procedure object
        """
        proc_dir = os.path.join(self._base_proc_dir, proc.name)
        if not os.path.exists(proc_name):
            os.makedirs(proc_dir)

        proc.write_and_verify(os.path.join(proc_dir, f"{proc.name}_procedure"))

    def load_proc(self, schema, proc_id):
        """ Loads a procedure by name """
        proc_dir = os.path.join(self._base_proc_dir, proc_id)
        if not os.path.exists(proc_dir):
            raise RuntimeError("Attempted to load a procedure from a directory that does not exist")

        proc_file = os.path.join(proc_dir, f"{proc_id}_procedure")
        self.proc_reader = Proc_Reader(schema, proc_file)

    def load_proc_history(self):
        """ Loads previous results of running the test procedure """
        pass

    def load_step(self, step_id):
        """ Gets the procedure step and starts all processes that needed to support it including
        polling readings and listening for controls from the user """
        pass

    def exe_step(self, step_id):
        """ Get an action from the test procedure and run the relevant function """
        step_result = Step_Result(passed=False, actions_taken=[])
        actions = self.proc_reader.get_actions()

        for act_num, action in enumerate(actions):
            action_type, fn, param_str = action.split(":")
            action_res = action_functions[action_type][fn](*literal_eval(param_str))
            if action_res.error == True:
                self.logger.error("Test step failed to execute correctly")

            if action_res.transmit == True:
                self.controller_com.send_action_result()

            step_result.actions_taken = step_result.action_taken + action_res

    def pause_proc(self):
        """ Pauses the procedure, saving the intermediate results """
        pass

    def cancel_proc(self):
        pass

    def save_step_res(self):
        pass

    def send_step_results(self):
        pass

    def _get_device(self):
        pass


def check_pressure_sensor(sensor_id, value, tolerance):
    logger.info(f"Checking pressure sensor: {sensor_id}")
    ar = Action_Result()

    readings = []
    votes = [False, False, False]
    pass_count = 0
    pass_result = None
    fail_result = None
    for vote in range(3):
        reading = poll_sensor(sensor_id)
        votes[vote] = isclose(value, reading, abs_tol=tolerance)

        if votes[vote]:
            pass_count = pass_count + 1
            pass_result = reading
        else:
            fail_result = reading

    action_success = True if pass_count >= 2 else False
    transmit = True
    result_tip = f"Pressure check results: {readings}"
    result_value = pass_result if pass_count >= 2 else fail_result

    return Action_Result(error=action_success, transmit=transmit,result_tip=result_tip,result_value=result_value)

    error: bool
    transmit: bool = False
    step_id: str = None
    result_tip: str
    action_taken: str = None
    result_value: str

def check_user_validate(display_str):
    logger.info(f"Waiting on user validation: {display_str}")