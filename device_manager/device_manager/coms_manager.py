import atexit
import copy
import yaml
from multiprocessing import Process, Lock, Manager, Queue
import time
import threading
import json
import os

import serial
import serial.tools.list_ports

FAULTY_PRESSURE_OFFSET = 3
FAILED_SENSOR_THRESHOLD = 5
DEBUG = 1

class Fake_COM:
    def __init__(self):
        pass

    def readline(self):
        return 'pressure_1038401923_0_112_112'

    def write(self, msg):
        print(msg)

def register_failed_sensor():
    pass

def validate_pressures(fault, p1, p2):
    if int(fault):
        return "ERR"

    i_p1 = float(p1)
    i_p2 = float(p2)

    # TODO: consider putting math elsewhere
    if abs(i_p1-i_p2) > FAULTY_PRESSURE_OFFSET:
        return "ERR"

    return (i_p1 + i_p2)/2


def read_pressure(reading_dict, fault_dict, serial_com):

    while(True):
        reading = serial_com.readline()
        r_type, sens_id, fault, p1, p2 = reading.split('_')

        if fault_dict.get(sens_id, 0) > FAILED_SENSOR_THRESHOLD:
            reading_dict[sens_id] = "FAULT"
            continue

        if int(fault):
            reading_dict[sens_id] = "FAULT"
            continue

        pressure_result = validate_pressures(fault, p1, p2)
        reading_dict[sens_id] = pressure_result

        if pressure_result == "ERR":
            fault_dict[sens_id] = fault_dict.get(sens_id, 0) + 1
            if fault_dict[sens_id] > FAILED_SENSOR_THRESHOLD:
                reading_dict[sens_id] = "FAULT"

def write_pressure(write_buffer, serial_com):
    while(True):
        while(not write_buffer.empty()):
            msg = write_buffer.get()
            serial_com.write(msg.encode('utf-8'))
        time.sleep(1)

def clean_rx_tx(rx_thread):
    rx_thread.terminate()

def start_rx_tx(reading_dict, fault_dict, write_buffer):
    if DEBUG:
        serial_com = Fake_COM()
    else:
        serial_com = serial.Serial("COM4", baudrate=9600, timeout=5)

    rx_thread = threading.Thread(target=read_pressure, args=(reading_dict, fault_dict, serial_com,))
    tx_thread = threading.Thread(target=write_pressure, args=(write_buffer, serial_com,), daemon=True)

    rx_thread.start()
    tx_thread.start()

    rx_thread.join()


class COM_Manager:
    instance = None
    pressure_readings = None
    pressure_faults = None
    serial_com = None
    com_rx_tx_process = None
    com_read_process = None
    com_write_process = None
    write_buffer = None

    def __init__(self):
        if not COM_Manager.com_rx_tx_process:
            COM_Manager.pressure_readings = Manager().dict()
            COM_Manager.pressure_faults = Manager().dict()
            COM_Manager.write_buffer = Manager().Queue()
            COM_Manager.serial_com = None

            COM_Manager.com_rx_tx_process = Process(target=start_rx_tx, args=(COM_Manager.pressure_readings, COM_Manager.pressure_faults, COM_Manager.write_buffer,))
            COM_Manager.com_rx_tx_process.start()
            atexit.register(clean_rx_tx, rx_thread=COM_Manager.com_rx_tx_process)

        if not COM_Manager.instance:
            COM_Manager.instance = COM_Manager.__COM_Manager()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __str__(self):
        return str(self.instance)

    class __COM_Manager:
        def __init__(self, device_config_file=None):
            # TODO: base this on an env variable
            self._device_config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../device_config.json"))
            try:
                with open(self._device_config_file) as config_file:
                    self._device_config = json.load(config_file)
            except FileNotFoundError:
                self._device_config = {'devices':{}}

            self._root_config = device_config_file

            if device_config_file:
                self._device_config = self.load_devices_from_file(self._root_config)

        def get_readings(self, debug=False):
            """Return a dictionary with key,value pairs of pressure sensors to their
            most recent values"""
            readings = copy.deepcopy(COM_Manager.pressure_readings)

            return {self._device_config['devices'].get(p_uuid, p_uuid): v for p_uuid, v in readings.items()}

        def send_pneu_ctrl(self, signal):
            COM_Manager.write_buffer.put(signal)

        def _save_device_config(self):
            with open(self._device_config_file, 'w') as config_file:
                json.dump(self._device_config, config_file)

        def set_device_label(self, dev_uuid, dev_label):
            self._device_config['devices'][dev_uuid] = dev_label
            # TODO: check that the label is unique

            self._save_device_config()

        def update_device_label(self, old_label, dev_label):
            """Change a device label in the device config"""
            res = False

            for dev_id, label in self._device_config['devices'].items():
                if label == old_label:
                    self._device_config['devices'][dev_id] = dev_label
                    res = True
                    break

            self._save_device_config()
            return res

        def clear_device_label(self, label):
            if label == 'all':
                self._device_config['devices'] = {}
            else:
                for dev_id, l in self._device_config['devices'].items():
                    if l == label:
                        self._device_config['devices'].pop(dev_id)
                        break

            self._save_device_config()            

