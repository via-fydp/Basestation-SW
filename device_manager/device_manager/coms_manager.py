import copy
import yaml
from multiprocessing import Process, Lock, Manager, Queue
import time
import threading

import serial
import serial.tools.list_ports

FAULTY_PRESSURE_OFFSET = 3
FAILED_SENSOR_THRESHOLD = 5
DEBUG = 0

class Fake_COM:
    def __init__(self):
        pass

    def readline(self):
        return 'pressure_1_0_112_112'

def register_failed_sensor():
    pass

def validate_pressures(fault, p1, p2):
    if int(fault):
        return "ERR"

    i_p1 = float(p1)
    i_p2 = float(p2)

    if abs(i_p1-i_p2) > FAULTY_PRESSURE_OFFSET:
        return "ERR"

    return (i_p1 + i_p2)/2


def read_pressure(reading_dict, fault_dict, serial_com):
    print('Started Read')
    if DEBUG:
        com_in = Fake_COM()
    else:
        com_in = serial_com

    while(True):
        reading = com_in.readline()
        print(f'reading: {reading}')
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
        serial_com.write('abc_def'.encode('utf-8'))
        time.sleep(5)


def start_rx_tx(reading_dict, fault_dict, write_buffer):
    print('Starting rx tx')
    serial_com = serial.Serial("COM4", baudrate=9600, timeout=5)

    rx_thread = threading.Thread(target=read_pressure, args=(reading_dict, fault_dict, serial_com,))
    tx_thread = threading.Thread(target=write_pressure, args=(write_buffer, serial_com,))

    rx_thread.start()
    tx_thread.start()
    print('Started threads')

    tx_thread.join()
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
        print(COM_Manager.instance)
        print(COM_Manager.com_rx_tx_process)

        if not COM_Manager.com_rx_tx_process:
            # my_list = serial.tools.list_ports.comports()
            # print(my_list)

            COM_Manager.pressure_readings = Manager().dict()
            COM_Manager.pressure_faults = Manager().dict()
            COM_Manager.write_buffer = Queue()
            COM_Manager.serial_com = None

            COM_Manager.com_rx_tx_process = Process(target=start_rx_tx, args=(COM_Manager.pressure_readings, COM_Manager.pressure_faults, COM_Manager.write_buffer,))
            COM_Manager.com_rx_tx_process.start()
            # serial_com = serial.Serial("COM4", baudrate=9600, timeout=2)
            # serial_com.close()

        if not COM_Manager.instance:
            COM_Manager.instance = COM_Manager.__COM_Manager()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __str__(self):
        return str(self.instance)

    class __COM_Manager:
        def __init__(self, device_config_file=None):
            self._device_config = {}
            self._root_config = device_config_file

            if device_config_file:
                self._device_config = self.load_devices_from_file(self._root_config)

        def get_readings(self):
            readings = copy.deepcopy(COM_Manager.pressure_readings)
            return readings

        def send_pneu_ctrl(self, signal):
            pass


        # def load_devices_from_file(self, device_config_file):
        #     with open(device_config_file, 'r') as config_file:
        #         try:
        #             yaml.safe_load(config_file)
        #         except yaml.YAMLError as e:
        #             print(e)

