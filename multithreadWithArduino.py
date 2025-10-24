import serial.tools.list_ports
import time
import threading
from helper_functions import *

# Connecting to port used by arduino
ports = serial.tools.list_ports.comports()
ser = serial.Serial()
portsList = []
serialLock = threading.Lock()

use = "/dev/cu.usbmodem101"

# * Opening serial to communitcate with arduino
ser.baudrate = 9600
ser.port = use
ser.open()

# * Variable Initialization

# Number of channels to be filled
global N_CHANNELS
# Number of channels that have been filled
global P_CHANNEL_N

N_MOLDS = 2
N_CHANNELS = 4

PIPETTE = 0
LIQUID_REAGENT_1 = 1
LIQUID_REAGENT_2 = 2

ALIQUOT_SIZE = 0.95  # amount for mold
AIR_GAP = 0.05       # aliquot + air gap should be < pipette volume

P_CHANNEL_N = 0

# Variables that have to be passed to threaded helper functions
gloVars = [P_CHANNEL_N, N_CHANNELS]

# * Events to pause threads when necessary as dictated by arduino input
sonicationBegun = threading.Event()
idBegun = threading.Event()
unpaused = threading.Event()
unpaused.set()

# Used to stop reading serial when main loop is exited
inMainLoop = True

def fill_channel(P_CHANNEL_N, N_CHANNELS):
    # Is number of channels currently filled >= number of channels to be filled?
    if P_CHANNEL_N >= N_CHANNELS:
        raise RuntimeError("Can't dispense, the number of filled channels would exceed N_CHANNELS")
    # Is number of channels currently filled > the number of channels on the molds?
    if P_CHANNEL_N > 7:
        raise RuntimeError("Cannot dispense, all channels have already been filled")

    # Filling channel (if unpaused otherwise wait)
    unpaused.wait()
    time.sleep(5)

    P_CHANNEL_N = P_CHANNEL_N + 1
    print("Have filled " + str(P_CHANNEL_N) + " channels")
    return P_CHANNEL_N

def fill_channels(num, P_CHANNEL_N, N_CHANNELS):
    serialLock.acquire()
    ser.write("FILLING".encode('utf-8'))
    serialLock.release()
    print("Beginning fill channels")
    
    for channel in range(num):
        # Is number of channels currently filled >= number of channels to be filled?
        if P_CHANNEL_N >= N_CHANNELS:
            break
        # Is number of channels currently filled > the number of channels on the molds?
        if P_CHANNEL_N > 7:
            raise RuntimeError("Cannot dispense, all channels have already been filled")

        # Filling channel (if unpaused otherwise wait)
        unpaused.wait()
        time.sleep(5)

        serialLock.acquire()
        ser.write("FILLED".encode('utf-8'))
        serialLock.release()


        P_CHANNEL_N = P_CHANNEL_N + 1
        print("Have filled " + str(P_CHANNEL_N) + " channels")
    
    time.sleep(2)
    serialLock.acquire()
    ser.write("NOTFILLING".encode('utf-8'))
    serialLock.release()

    print("Ending fill channels")
    return P_CHANNEL_N

def channel_and_pipette(num, gloVars):
    # ! Add logic to display preparing on second line
    let_vial_go()

    get_pipette()
    
    uncap_vial()

    P_CHANNEL_N = gloVars[0]
    N_CHANNELS = gloVars[1]


    i = fill_channels(num, P_CHANNEL_N, N_CHANNELS)
    gloVars[0] = i

def channel(num, gloVars):
    # ! Add logic to display preparing on second line
    let_vial_go()
    P_CHANNEL_N = gloVars[0]
    N_CHANNELS = gloVars[1]

    i = fill_channels(num, P_CHANNEL_N, N_CHANNELS)
    gloVars[0] = i

# Function that simulates robot actions from setup through sonication
def beginToSon(sample_num):
    # * disarm_heater(2)
    # elevator.goto_slot(sample_num)
    
    # ! Have first line displaying setting up
    print("Positioning elevator")
    time.sleep(1)
    
    # * 1. Get Vial
    unpaused.wait()
    get_vial(sample_num)

    # * 2. Uncap Vial
    unpaused.wait()
    cap_height = uncap_vial()
    
    # * 3. Fill Vial
    # GC2
    unpaused.wait()
    fill_GC2()
    # Dispense DCPD
    unpaused.wait()
    dispense_DCDP()
    
    # * 4. Recap Vial & Mix in TBP
    unpaused.wait()
    recapMixTBP(cap_height)
    
    unpaused.wait()

    # * 5. Round 1 Mix & Dry
    #c9.delay(180) # 3 min
    unpaused.wait()
    if ((sample_num == 0) | (N_MOLDS < 2)):
        ser.write("READYFORS".encode('utf-8'))

        sonicationBegun.wait()
        print("Sonication begun")
        sonicationBegun.clear()
        
        ser.write("SONICATING".encode('utf-8'))
        for i in range(10):
            unpaused.wait()
            sonicate(1)
    else:
        serialLock.acquire()
        ser.write("READYFORID".encode('utf-8'))
        serialLock.release()
        idBegun.wait()
        thread1 = threading.Thread(target=channel_and_pipette, args=(2, gloVars))
        thread1.start()

        time.sleep(0.5)

        serialLock.acquire()
        ser.write("READYFORS".encode('utf-8'))
        serialLock.release()
        sonicationBegun.wait()
        sonicationBegun.clear()
        print("Sonication begun")

        serialLock.acquire()
        ser.write("SONICATING".encode('utf-8'))
        serialLock.release()
        for i in range(10):
            unpaused.wait()
            sonicate(1)
    
        thread1.join()
        time.sleep(1.5)

    unpaused.wait()
    ser.write("DRYING".encode('utf-8'))
    dry()
    ser.write("NOTDRYING".encode('utf-8'))
    # * 6. Round 2 Mix & Dry
    if ((sample_num == 0) | (N_MOLDS < 2)):
        unpaused.wait()

        for i in range(4):
            unpaused.wait()
            sonicate(1)
        
        unpaused.wait()
        ser.write("DRYING".encode('utf-8'))
        dry()

 

        unpaused.wait()
        serialLock.acquire()
        ser.write("DONESON".encode('utf-8'))
        serialLock.release()

        unpaused.wait()
        place_vial_in_safe()
    else:
        time.sleep(2)
        unpaused.wait()
        thread2 = threading.Thread(target=channel, args=(1, gloVars))
        thread2.start()

        unpaused.wait()
        for i in range(4):
            unpaused.wait()
            sonicate(1)

        thread2.join()
        idBegun.clear()

        time.sleep(1.5)

        unpaused.wait()
        ser.write("DRYING".encode('utf-8'))
        dry()



        serialLock.acquire()
        ser.write("DONESON".encode('utf-8'))
        print("Serial message sent - DONESON")
        time.sleep(1)
        serialLock.release()

    sonicationBegun.clear()
    time.sleep(1)

# Function that simulates robot actions from intake and dispense through clean up
def i_and_d_to_end():
    print("Beginning I_and_D_to_end")
    
    serialLock.acquire()
    ser.write("READYFORID".encode('utf-8'))
    serialLock.release()
    idBegun.wait()
    
    # Tell the arduino that we have started i&d
    unpaused.wait()
    serialLock.acquire()
    ser.write("FILLING".encode('utf-8'))
    serialLock.release()

    # * 9. Intake & Dispense Solution into Channels
    for channel in range(gloVars[0], N_CHANNELS):
        unpaused.wait()
        if gloVars[0] > 7:
            raise RuntimeError("Cannot dispense, all channels have already been filled")
        fill_channel(gloVars[0], N_CHANNELS)
        serialLock.acquire()
        ser.write("FILLED".encode('utf-8'))
        serialLock.release()
        gloVars[0] += 1
    gloVars[0] = 0

    idBegun.clear()
    time.sleep(2)
    # ser.write("NOTFILLING".encode('utf-8'))
    
    # Preheat the enviro chamber
    # ! Will probably need to move up to compenstate for threading time savings

    ser.write("PROMPTING".encode('utf-8'))
    unpaused.wait()
    frontT = threading.Thread(target=prompt_front)
    frontT.start()

    # * 10. Remove Pipette
    unpaused.wait()
    print("Removing pipette")
    time.sleep(2)
    
    # * 11. Recap Vial
    unpaused.wait()
    recap_vial()

    unpaused.wait()
    print("Returning vial to rack")
    unpaused.wait() 
    time.sleep(2)
   
    # * 12. Return Vial to Rack
    frontT.join()
    
    unpaused.wait()
    print("Unloading mold")

    serialLock.acquire()
    ser.write("MOLDDONE".encode('utf-8'))
    serialLock.release()

    unpaused.wait()
    print("Setting up new mold")
    time.sleep(1)

# * Function that reads statements printed to serial
    # Listens for input from arduino
def readSerial():
    global sonicationBegun
    global idBegun
    global inMainLoop

    while inMainLoop:
        if (ser.in_waiting > 0):
            data = ser.read(ser.in_waiting)
            stringData = data.decode('utf-8').strip()
            
            if stringData == "SONICATIONBEGUN":
                sonicationBegun.set()
            elif stringData == "IDBEGUN":
                idBegun.set()
            elif stringData == "PAUSED":
                unpaused.clear()
                print("PAUSED")
            elif stringData == "UNPAUSED":
                unpaused.set()
                print("Unpaused")

# * ALL HEATERS RESET, THEN SET ENVIRO CHAMBER TO 30°C

# Beginning reading the serial
serialThread = threading.Thread(target=readSerial)
serialThread.start()



# * Main loop
    # Runs sample prep for N_MOLDS number of samples
for sample_num in range(N_MOLDS):
    beginToSon(sample_num=sample_num)

    if ((sample_num == 0) & (N_MOLDS > 1)):
        continue

    i_and_d_to_end()
    
    if ((sample_num == N_MOLDS - 1) & (N_MOLDS > 1)):
        place_vial_in_safe()
        uncap_vial()
        i_and_d_to_end()
    

inMainLoop = False
serialThread.join()
print("End of program")