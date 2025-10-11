import serial.tools.list_ports
import time
import threading
from helper_functions import *

# Connecting to port used by arduino
ports = serial.tools.list_ports.comports()
ser = serial.Serial()
portsList = []

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
    ser.write("FILLING".encode('utf-8'))
    time.sleep(15)    
    ser.write("FILLED".encode('utf-8'))

    P_CHANNEL_N = P_CHANNEL_N + 1
    print("Have filled " + str(P_CHANNEL_N) + " channels")
    return P_CHANNEL_N

def fill_channels(num, P_CHANNEL_N, N_CHANNELS):
    for channel in range(num):
        # Is number of channels currently filled >= number of channels to be filled?
        if P_CHANNEL_N >= N_CHANNELS:
            break
        # Is number of channels currently filled > the number of channels on the molds?
        if P_CHANNEL_N > 7:
            raise RuntimeError("Cannot dispense, all channels have already been filled")

        # Filling channel (if unpaused otherwise wait)
        unpaused.wait()
        ser.write("FILLING".encode('utf-8'))
        time.sleep(15)

        ser.write("FILLED".encode('utf-8'))
        P_CHANNEL_N = P_CHANNEL_N + 1
        print("Have filled " + str(P_CHANNEL_N) + " channels")
        
    return P_CHANNEL_N

def channel_and_pipette(num, gloVars):
    let_vial_go()

    get_pipette()
    
    uncap_vial()

    P_CHANNEL_N = gloVars[0]
    N_CHANNELS = gloVars[1]

    i = fill_channels(num, P_CHANNEL_N, N_CHANNELS)
    gloVars[0] = i

def channel(num, gloVars):
    let_vial_go()
    P_CHANNEL_N = gloVars[0]
    N_CHANNELS = gloVars[1]

    i = fill_channels(num, P_CHANNEL_N, N_CHANNELS)
    gloVars[0] = i

def mix_dry(num: int):
    # Wait until unpaused to continue
    unpaused.wait()

    # * If it is the first sample or there is only one mold to prep, don't thread
    if ((sample_num == 0) | (N_MOLDS < 2)):
        # Tell arduino we're ready for sonication
        ser.write("READYFORS".encode('utf-8'))
        # Wait for input from arduino telling us to start sonication
        sonicationBegun.wait()
        print("Sonication begun")
        sonicationBegun.clear()

        # Actually sonicate
        ser.write("SONICATING".encode('utf-8'))
        sonicate(30)

        # Tell arduino we're done sonicating
        ser.write("DONESON".encode('utf-8'))

        # If second round dry vial and place it in the safe area
        if (num == 2):
            unpaused.wait()
            dry()

            unpaused.wait()
            place_vial_in_safe()

    # * Otherwise use threads
    else:
        # Tell arduino we're ready for intaking and dispensing
        ser.write("READYFORID".encode('utf-8'))
        # Wait for input from arduino telling us to start intaking and dispensing
        idBegun.wait()

        # * Open thread to start intaking and dispensing
        thread1 = threading.Thread(target=channel_and_pipette, args=(num, gloVars))
        thread1.start()

        # * At the same time
        if (num == 1):
            # In main thread tell arduino we're ready for sonication
            ser.write("READYFORS".encode('utf-8'))

            # Wait for input from arduino telling us we're ready for sonication
            sonicationBegun.wait()
            print("Sonication begun")
            sonicationBegun.clear()

            # Tell arduino we've started sonicating
            ser.write("SONICATING".encode('utf-8'))
            sonicate(30)
        else:
            sonicate(10)
        
        # And now tell it we're done
        ser.write("DONESON".encode('utf-8'))

        # Rejoin threads, both sonication and I&D are done
        thread1.join()

    # Dry vial (once unpaused)
    unpaused.wait()
    dry()

# Function that simulates robot actions from setup through sonication
def beginToSon(sample_num):
    # * Beginning set-up
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
    # TBP
    
    # * 4. Recap Vial & Mix in TBP
    unpaused.wait()
    recapMixTBP(cap_height)
    
    unpaused.wait()

    # * 5. Round 1 Mix & Dry
    mix_dry(1)
    
    # * 6. Round 2 Mix & Dry
    mix_dry(2)

    sonicationBegun.clear()

# Function that simulates robot actions from intake and dispense through clean up
def i_and_d_to_end():
    # * 9. Intake & Dispense Solution into Channels
    for channel in range(gloVars[0], N_CHANNELS):
        unpaused.wait()
        if gloVars[0] > 7:
            raise RuntimeError("Cannot dispense, all channels have already been filled")
        fill_channel(gloVars[0], N_CHANNELS)
        gloVars[0] += 1
    gloVars[0] = 0

    idBegun.clear()
    
    # Preheat the enviro chamber
    # ! Will probably need to move up to compenstate for threading time savings

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
    time.sleep(10)
   
    # * 12. Return Vial to Rack
    frontT.join()
    
    unpaused.wait()
    print("Unloading mold")

    ser.write("MOLDDONE".encode('utf-8'))

    unpaused.wait()
    print("Setting up new mold")

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
    
    ser.write("READYFORID".encode('utf-8'))
    idBegun.wait()
    i_and_d_to_end()
    
    if ((sample_num == N_MOLDS - 1) & (N_MOLDS > 1)):
        place_vial_in_safe()
        uncap_vial()
        i_and_d_to_end()
    

inMainLoop = False
serialThread.join()
print("End of program")
