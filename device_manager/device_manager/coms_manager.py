import atexit
import copy
import yaml
import logging
from multiprocessing import Process, Lock, Manager, Queue
import time
import threading
import json
import os

import serial
import serial.tools.list_ports

FAULTY_PRESSURE_OFFSET = 300
FAILED_SENSOR_THRESHOLD = 5
SIGNAL_HISTORY = 50
DEBUG = 0

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
        return "FAULT"

    i_p1 = float(p1)
    i_p2 = float(p2)

    # TODO: consider putting math elsewhere
    if abs(i_p1-i_p2) > FAULTY_PRESSURE_OFFSET:
        return "ERR"

    return (i_p1 + i_p2)/2

def register_signal(context, signal):
    sig_queue = context['signals_list']

    if len(sig_queue) >= SIGNAL_HISTORY:
        sig_queue.pop(0)

    sig_queue.append(signal)

def record_pressure(context, signal):
    _, sens_uuid, fault, p1, p2 = signal.split('_')
    fault_dict = context['fault_dict']
    reading_dict = context['reading_dict']['pressures']

    if fault_dict.get(sens_uuid, 0) > FAILED_SENSOR_THRESHOLD:
        reading_dict[sens_uuid] = "FAULT"
        return

    pressure_result = validate_pressures(fault, p1, p2)
    reading_dict[sens_uuid] = pressure_result

    if pressure_result == "ERR":
        fault_dict[sens_uuid] = fault_dict.get(sens_uuid, 0) + 1
        if fault_dict[sens_uuid] > FAILED_SENSOR_THRESHOLD:
            reading_dict[sens_uuid] = "FAULT"

    context['reading_dict']['pressures'] = reading_dict

def record_battery(context, signal):
    _, device_uuid, val, _, charging = signal.split('_')
    reading_dict = context['reading_dict']['battery']
    reading_dict[device_uuid] = {'value': val, 'charging': charging}
    context['reading_dict']['battery'] = reading_dict

def register_signal_ack_nack(context, sig):
    pass

def no_valid_signal(*args):
    print("Signal invalid")

signal_func = {
    'pressure': record_pressure,
    'battery': record_battery,
    'ack': register_signal_ack_nack,
    'nack': register_signal_ack_nack,
}

def read_signals(reading_dict, signals_queue, fault_dict, serial_com):
    logger = logging.getLogger("COM_logger")

    context = {
        'reading_dict': reading_dict,
        'signals_list': signals_queue,
        'fault_dict': fault_dict,
    }

    while(True):
        try:
            signal = serial_com.readline().decode('utf-8').strip('\n')
            if signal:
                logger.debug(f'Signal: {signal}')
                s_type, args = signal.split('_', 1)

                try:
                    register_signal(context, signal)
                    signal_func.get(s_type, no_valid_signal)(context, signal)
                except Exception as err:
                    logger.error(f"Error executing function on signal {signal}: {err}")
        except Exception as err:
            serial_com.reset_input_buffer()
            logger.error(f"Error reading serial data:\n{err}")


def write_pressure(write_buffer, serial_com):
    while(True):
        while(not write_buffer.empty()):
            msg = write_buffer.get()
            serial_com.write(f'{msg}\n'.encode('utf-8'))
        time.sleep(0.2)

def clean_rx_tx(rx_thread):
    rx_thread.terminate()

def start_rx_tx(reading_dict, signals_queue, fault_dict, write_buffer):
    """ Start threads to read from and write to the serial port connected to
    the embedded controller
    """
    logger = logging.getLogger("COM_logger")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('/fydp/logging.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    if DEBUG:
        serial_com = Fake_COM()
    else:
        connection = 0
        while not connection:
            try:
                serial_com = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
                signal = serial_com.readline()
                if signal:
                    connection = 1
                    break
                print("No data over serial")
            except Exception as err:
                logger.error(f"Error creating serial port: {err}")
                time.sleep(2)

    rx_thread = threading.Thread(
        target=read_signals,
        args=(reading_dict, signals_queue, fault_dict, serial_com,)
        )
    tx_thread = threading.Thread(
        target=write_pressure,
        args=(write_buffer, serial_com,), daemon=True
        )

    rx_thread.start()
    tx_thread.start()

    rx_thread.join()


class COM_Manager:
    instance = None
    device_readings = None
    embedded_signals = None
    sent_signals = None
    pressure_faults = None
    serial_com = None
    com_rx_tx_process = None
    com_read_process = None
    com_write_process = None
    write_buffer = None
    signal_lock = None

    def __init__(self):
        if not COM_Manager.com_rx_tx_process:
            COM_Manager.device_readings = Manager().dict()
            COM_Manager.device_readings['pressures'] = {}
            COM_Manager.device_readings['battery'] = {}
            COM_Manager.signal_lock = Lock()
            COM_Manager.embedded_signals = Manager().list()
            COM_Manager.pressure_faults = Manager().dict()
            COM_Manager.write_buffer = Manager().Queue()
            COM_Manager.serial_com = None

            COM_Manager.com_rx_tx_process = Process(target=start_rx_tx, args=(
                COM_Manager.device_readings,
                COM_Manager.embedded_signals,
                COM_Manager.pressure_faults,
                COM_Manager.write_buffer,)
            )
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

        def get_readings(self):
            """Return a dictionary with key,value pairs of pressure sensors to their
            most recent values"""
            pressure_readings = copy.deepcopy(COM_Manager.device_readings)['pressures']

            return {self._device_config['devices'].get(p_uuid, p_uuid): v for p_uuid, v in pressure_readings.items()}

        def get_battery(self):
            """Return a dictionary with key,value pairs of devices to their
            current battery values"""
            battery_readings = copy.deepcopy(COM_Manager.device_readings)['battery']

            return {self._device_config['devices'].get(p_uuid, p_uuid): v for p_uuid, v in battery_readings.items()}

        def get_last_embedded_signals(self):
            """Return a list of the signals in the embedded signal queue"""
            signals = copy.deepcopy(COM_Manager.embedded_signals)

            return signals

        def send_pneu_ctrl(self, signal):
            COM_Manager.write_buffer.put(signal)

        def _save_device_config(self):
            with open(self._device_config_file, 'w') as config_file:
                json.dump(self._device_config, config_file)

        def set_device_label(self, dev_uuid, dev_label):
            self._device_config['devices'][dev_uuid] = dev_label

            self._save_device_config()

        def update_device_label(self, old_label, dev_label):
            """Change a device label in the device config"""
            res = False

            # replace an existing label
            for dev_id, label in self._device_config['devices'].items():
                if label == old_label:
                    self._device_config['devices'][dev_id] = dev_label
                    res = True
                    break

            # make a new label
            if not res:
                self._device_config['devices'][old_label] = dev_label

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

