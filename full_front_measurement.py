"""from north import NorthC9
from Locator import *

from powder_settings import *
from dispensing_helper_functions import *
from temperature_control_v2 import *
from elevator_commands import *
from mold_linear_slide import *
from pick_and_place_helper_functions import *
from lepton_recording import LeptonRecorder"""
import time
import threading
from helper_functions import *

"""recorder = LeptonRecorder()
elevator = MoldElevator(port='COM5')"""

#Variable Initialization
global N_CHANNELS
global P_CHANNEL_N

N_MOLDS = 2
N_CHANNELS = 8

PIPETTE = 0
LIQUID_REAGENT_1 = 1
LIQUID_REAGENT_2 = 2

ALIQUOT_SIZE = 0.95  # amount for mold
AIR_GAP = 0.05       # aliquot + air gap should be < pipette volume

P_CHANNEL_N = 0

gloVars = [P_CHANNEL_N, N_CHANNELS]

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

def beginToSon(sample_num):
    # * disarm_heater(2)
    # elevator.goto_slot(sample_num)
    print("Positioning elevator")
    time.sleep(1)
    
    # * 1. Get Vial
    get_vial(sample_num)

    # * 2. Uncap Vial
    cap_height = uncap_vial()
    
    # * 3. Fill Vial
    # GC2
    fill_GC2()
    # Dispense DCPD
    dispense_DCDP()
    # TBP
    #     c9.move_carousel(112.5, 88.5)
    #     dispense(c9, LIQUID_REAGENT_2, 0.00205)
    #     c9.move_carousel(202.5, 88.5)
    #     c9.delay(5)
    """c9.move_carousel(0, 0)"""
    
    # * 4. Recap Vial & Mix in TBP
    recapMixTBP(cap_height)
    
    # * 5. Round 1 Mix & Dry
    #c9.delay(180) # 3 min
    if ((sample_num == 0) | (N_MOLDS < 2)):
        sonicate(30)
    else:
        thread1 = threading.Thread(target=channel_and_pipette, args=(2, gloVars))
        thread1.start()

        sonicate(30)
    
        thread1.join()

    dry()
    
    # * 6. Round 2 Mix & Dry
    if ((sample_num == 0) | (N_MOLDS < 2)):
        sonicate(30)
        
        dry()

        place_vial_in_safe()
    else:
        thread2 = threading.Thread(target=channel, args=(1, gloVars))
        thread2.start()

        sonicate(10)

        thread2.join()

        dry()

    #c9.delay(1)
    #c9.delay(60) # 1 min

    # Reset after sonication
    """c9.reduce_axis_position(c9.GRIPPER)  # mod gripper position by 4000
    c9.goto_safe(home)"""
    
    # c9.home_axis(c9.GRIPPER, wait = False)

def i_and_d_to_end():
    # * 9. Intake & Dispense Solution into Channels
    for channel in range(gloVars[0], N_CHANNELS):
        if gloVars[0] > 7:
            raise RuntimeError("Cannot dispense, all channels have already been filled")
        fill_channel(gloVars[0], N_CHANNELS)
        gloVars[0] += 1
    gloVars[0] = 0
    
    # Preheat the enviro chamber
    # ! Will probably need to move up to compenstate for threading time savings
    """activate_heater(2, 200)"""

    frontT = threading.Thread(target=prompt_front)
    frontT.start()

    # * 10. Remove Pipette
    # c9.goto_safe(p_tip_remover_approach)
    # c9.goto(p_remover, accel=5)
    # c9.move_z(292) # move up to max height to dislodge the tip
    """remove_pipette(c9)"""
    print("Removing pipette")
    time.sleep(2)
    
    # * 11. Recap Vial
    recap_vial()

    print("Returning vial to rack")
    time.sleep(10)
    """c9.goto_safe(vial_clamp)
    # * 12. Return Vial to Rack
    c9.close_gripper()
    c9.open_clamp()
    c9.goto_safe(vial_rack_lifted[sample_num])
    c9.open_gripper()"""

    frontT.join()
    
    """unload_mold(c9)"""
    print("Unloading mold")

    print("Setting up new mold")


# * ALL HEATERS RESET, THEN SET ENVIRO CHAMBER TO 30°C
"""disarm_heater(1)
disarm_heater(2)
disarm_heater(3)
time.sleep(0.2)
activate_heater(3, 30)"""

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
    
    i_and_d_to_end()
    
    if ((sample_num == N_MOLDS - 1) & (N_MOLDS > 1)):
        place_vial_in_safe()
        uncap_vial()
        i_and_d_to_end()
    
"""deactivate_heater(3)
elevator.home()
unload_powder_cartridge(c9, sdepeed = 1, position = powder_base_left)
c9.goto_safe(home)"""
print("End of program")