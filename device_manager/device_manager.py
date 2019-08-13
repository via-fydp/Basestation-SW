import yaml

class Device_Manager():

    def __init__(self, device_config_file=None):
        self._device_config = {}
        self._root_config = device_config_file

        if device_config_file:
            self._device_config = self.load_devices_from_file(self._root_config)

    def load_devices_from_file(self, device_config_file):
        with open(device_config_file, 'r') as config_file:
            try:
                yaml.safe_load(config_file)
            except yaml.YAMLError as e:
                print(e)

    def get_BT_id(self, device_name):
        """ Get the device id for Bluetooth communication based on device name """
        return self._device_config[device_name]['BT_ID']

