import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
portsList = []

for one in ports:
    portsList.append(str(one))
    print(str(one))

use = "/dev/cu.usbmodem101"

serialInst.baudrate = 9600
serialInst.port = use
serialInst.open()

while True:
    command = input("Ardunio Command (ON/OFF/exit): ")
    serialInst.write(command.encode('utf-8'))

    if command == 'exit':
        exit()