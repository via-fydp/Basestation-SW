## Starting the Server
To normally start the server, the basestation must be connected to a power supply and the basestation power switch turned on. Once power is supplied to the system, the server PC will automatically boot and start the web server.

## Quick Reference
- Network password (should be changed): 06231293
- Router IP (for administration): 192.168.0.1
- Router admin credentials: admin/admin

- Server IP: 192.168.0.100
- Server PC login credentials: via/viarail
- SSH: via@192.168.0.100

## Connecting to the Network
The local network is hosted using a TP-Link AC1200 router currently with default settings. Additional documentation on conifguration of this router can be found from TP-Link's documentation.

## Router Settings
The router has been set to assign a static IP to the server of 192.168.0.100. No additional security or routing settings have been configured. The router supports additional DNS settings if desired.

## Server Startup Services
Two startup services have been added to the server's systemd folder that are used to start up the web service on boot and can be found in the system_services folder of this Git repository.

## Web Server Behaviour
A RESTful web service is hosted by the server using the Python3 Flask web framework and available by connecting to 192.168.0.100:5000/server_endpoint. A useful test to see if the server is running is to query /active_user or /get_readings, which should provide responses regardless of whether the server has additional system data. Documentation on additional endpoints and behaviour can be found in the engineering design specification document prepared for the system.

The core web framework code is located in the server_manager module found in this Git repository.

## Server Serial Communication
The server uses a serial connection to a development board in order to receive pressure readings and transmit pneumatic actuation signals. Documentation on the signals transmitted through the system can be found in the design specification for the system. Relevant Python code is found in the device_manager module of this Git repository. In short, the device manager contains a COM_Manager class, which is a singleton used to interact with the embedded board. The COM_Manager spins off a separate process to manage serial communications with separate rx/tx threads.

The COM_Manageer singleton provides helper functions to interact with share memory that is used to retrieve pressure readings and well as manage a message write queue. Example usage can be found throughout the server_manager module.

## Known Issues
- Due to a bug with the TI board used for the development of the system, the embedded board does not present a valid COM port on power-up when connected to a PC, meaning that the server cannot engage with the embedded system or WPSUs by default. The current workaroud for this is to leave the embedded board unplugged during system startup. Once a response is seen from the web service, to verify that the server has completed booting, the board can be plugged into the USB port of the server. With this procedure, the TI board will present a valid COM port. The same is true of a personal computer used for development 
- Currently pressure readings are not set to expire, meaning that if a pressure sensor disconnects, the pressure reading will not expire. This can be updated easily is software.