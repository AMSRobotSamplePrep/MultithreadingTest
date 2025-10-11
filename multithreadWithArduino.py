import serial.tools.list_ports
import time
import threading
from helper_functions import *

ports = serial.tools.list_ports.comports()
ser = serial.Serial()
portsList = []

use = "/dev/cu.usbmodem101"

ser.baudrate = 9600
ser.port = use
ser.open()

"""from north import NorthC9
from Locator import *

from powder_settings import *
from dispensing_helper_functions import *
from temperature_control_v2 import *
from elevator_commands import *
from mold_linear_slide import *
from pick_and_place_helper_functions import *
from lepton_recording import LeptonRecorder"""

"""recorder = LeptonRecorder()
elevator = MoldElevator(port='COM5')"""

#Variable Initialization
global N_CHANNELS
global P_CHANNEL_N

N_MOLDS = 2
N_CHANNELS = 4

PIPETTE = 0
LIQUID_REAGENT_1 = 1
LIQUID_REAGENT_2 = 2

ALIQUOT_SIZE = 0.95  # amount for mold
AIR_GAP = 0.05       # aliquot + air gap should be < pipette volume

P_CHANNEL_N = 0

gloVars = [P_CHANNEL_N, N_CHANNELS]

sonicationBegun = threading.Event()
idBegun = threading.Event()
unpaused = threading.Event()
unpaused.set()
inMainLoop = True

# Robot Initialization
# c9 = NorthC9('sim') # FOR SIMULATION RUN

# * Creating Instance of NorthC9
"""c9 = NorthC9('A', network_serial = "FT6VDV77")
c9.default_vel = 25 #  %
p2 = NorthC9('C', network = c9.network)"""

"""c9.get_info()
p2.get_info()"""

"""# Testing pumps
init_system(c9, PIPETTE, LIQUID_REAGENT_1, LIQUID_REAGENT_2)
# Setting powder cartridge up
load_powder_cartridge(c9, speed = 1, position = powder_base_left)
init_powder(p2)
# Resetting elevator
elevator.home()"""

def fill_channel(P_CHANNEL_N, N_CHANNELS):
    if P_CHANNEL_N >= N_CHANNELS:
        raise RuntimeError("Can't dispense, the number of filled channels would exceed N_CHANNELS")
    if P_CHANNEL_N > 7:
        raise RuntimeError("Cannot dispense, all channels have already been filled")
    """c9.goto_safe(p_vial_clamp)
    c9.aspirate_ml(PIPETTE, ALIQUOT_SIZE)
    c9.move_z(180)  # should be just out of vial
    c9.aspirate_ml(PIPETTE, AIR_GAP)  # draw air gap to prevent drips
    c9.goto_safe(p_mold_loading[P_CHANNEL_N])
    c9.dispense_ml(PIPETTE, ALIQUOT_SIZE + AIR_GAP)"""

    unpaused.wait()
    time.sleep(15)
    P_CHANNEL_N = P_CHANNEL_N + 1
    print("Have filled " + str(P_CHANNEL_N) + " channels")
    return P_CHANNEL_N

def fill_channels(num, P_CHANNEL_N, N_CHANNELS):
    for channel in range(num):
        if P_CHANNEL_N >= N_CHANNELS:
            break
        if P_CHANNEL_N > 7:
            raise RuntimeError("Cannot dispense, all channels have already been filled")
        """c9.goto_safe(p_vial_clamp)
        c9.aspirate_ml(PIPETTE, ALIQUOT_SIZE)
        c9.move_z(180)  # should be just out of vial
        c9.aspirate_ml(PIPETTE, AIR_GAP)  # draw air gap to prevent drips
        c9.goto_safe(p_mold_loading[P_CHANNEL_N])
        c9.dispense_ml(PIPETTE, ALIQUOT_SIZE + AIR_GAP)"""

        unpaused.wait()
        time.sleep(15)
        P_CHANNEL_N = P_CHANNEL_N + 1
        print("Have filled " + str(P_CHANNEL_N) + " channels")
        
    return P_CHANNEL_N

def channel_and_pipette(num, gloVars):
    let_vial_go()
    # c9.goto_safe(p_rack_side[sample_num])
    print("Getting pipette")

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

def beginToSon(sample_num):
    # * disarm_heater(2)
    # elevator.goto_slot(sample_num)
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
    #     c9.move_carousel(112.5, 88.5)
    #     dispense(c9, LIQUID_REAGENT_2, 0.00205)
    #     c9.move_carousel(202.5, 88.5)
    #     c9.delay(5)
    """c9.move_carousel(0, 0)"""
    
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
        sonicate(30)
        ser.write("DONESON".encode('utf-8'))
    else:
        ser.write("READYFORID".encode('utf-8'))
        idBegun.wait()
        thread1 = threading.Thread(target=channel_and_pipette, args=(2, gloVars))
        thread1.start()

        ser.write("READYFORS".encode('utf-8'))
        sonicationBegun.wait()
        sonicationBegun.clear()
        print("Sonication begun")

        ser.write("SONICATING".encode('utf-8'))
        sonicate(30)
        ser.write("DONESON".encode('utf-8'))
    
        thread1.join()

    unpaused.wait()
    dry()
    
    # * 6. Round 2 Mix & Dry
    if ((sample_num == 0) | (N_MOLDS < 2)):
        unpaused.wait()
        sonicationBegun.wait()
        print("Sonication begun")
        sonicationBegun.clear()
        
        ser.write("SONICATING".encode('utf-8'))
        sonicate(30)
        ser.write("DONESON".encode('utf-8'))
        
        unpaused.wait()
        dry()

        unpaused.wait()
        place_vial_in_safe()
    else:
        unpaused.wait()
        ser.write("READYFORID".encode('utf-8'))
        idBegun.wait()
        thread2 = threading.Thread(target=channel, args=(1, gloVars))
        thread2.start()

        unpaused.wait()
        ser.write("SONICATING".encode('utf-8'))
        sonicate(10)
        ser.write("DONESON".encode('utf-8'))

        thread2.join()

        unpaused.wait()
        dry()

    sonicationBegun.clear()

    #c9.delay(1)
    #c9.delay(60) # 1 min

    # Reset after sonication
    """c9.reduce_axis_position(c9.GRIPPER)  # mod gripper position by 4000
    c9.goto_safe(home)"""
    
    # c9.home_axis(c9.GRIPPER, wait = False)

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
    """activate_heater(2, 200)"""

    unpaused.wait()
    frontT = threading.Thread(target=prompt_front)
    frontT.start()

    # * 10. Remove Pipette
    # c9.goto_safe(p_tip_remover_approach)
    # c9.goto(p_remover, accel=5)
    # c9.move_z(292) # move up to max height to dislodge the tip
    """remove_pipette(c9)"""
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
    """c9.goto_safe(vial_clamp)
    # * 12. Return Vial to Rack
    c9.close_gripper()
    c9.open_clamp()
    c9.goto_safe(vial_rack_lifted[sample_num])
    c9.open_gripper()"""

    frontT.join()
    
    """unload_mold(c9)"""
    unpaused.wait()
    print("Unloading mold")

    unpaused.wait()
    print("Setting up new mold")

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
"""disarm_heater(1)
disarm_heater(2)
disarm_heater(3)
time.sleep(0.2)
activate_heater(3, 30)"""
serialThread = threading.Thread(target=readSerial)
serialThread.start()

#Begin Routine
for sample_num in range(N_MOLDS):
    beginToSon(sample_num=sample_num)

    if ((sample_num == 0) & (N_MOLDS > 1)):
        continue
    
    # * 7. Uncap Vial
    # ! Update to take vial from safe area not directly from sonicator
    
    # * 8. Get Pipette
    # c9.goto_safe(p_rack_side[sample_num])
    # Parallel code gets pipette and starts dispensing into channels during sonication
    
    ser.write("READYFORID".encode('utf-8'))
    idBegun.wait()
    i_and_d_to_end()
    
    if ((sample_num == N_MOLDS - 1) & (N_MOLDS > 1)):
        place_vial_in_safe()
        uncap_vial()
        i_and_d_to_end()
    
"""deactivate_heater(3)
elevator.home()
unload_powder_cartridge(c9, sdepeed = 1, position = powder_base_left)
c9.goto_safe(home)"""
inMainLoop = False
serialThread.join()
print("End of program")
