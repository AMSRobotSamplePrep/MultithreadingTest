import time

def home_pump_N2(pump_num, speed_code = 12):
    """c9.home_pump(pump_num)
    if not c9.sim:
        c9.send_com_msg(0, b'/' + str(pump_num+1).encode(encoding='charmap') + b'N2R\x0D')  # set to increment mode N2, must be done every power cycle
    c9.set_pump_speed(pump_num, speed_code)"""


# * Functions I created to simplify main for loop
def get_vial(sample_num: int):
    """c9.goto_safe(vial_rack_lifted[sample_num])
    c9.close_gripper()
    c9.goto_safe(vial_clamp)
    c9.close_clamp()"""
    print("Getting vial") 
    time.sleep(2)


def uncap_vial():
    """uncap(c9)
    cap_height = c9.get_axis_position(c9.Z_AXIS)
    c9.goto_safe(home)  # get out of the way"""
    
    print("Uncapping vial and saving the cap height")
    time.sleep(0.5)
    return -1

def fill_GC2():
    """c9.open_clamp()
    c9.move_carousel(67.5, 75)
    cl_pow_dispense(c9, p2, 3.2, gc2_ps, False)
    c9.close_clamp()"""

    print("Filling GC2")
    #time.sleep(20)

def dispense_DCDP():
    """c9.move_carousel(0, 0)
    c9.move_carousel(45, 80)
    dispense(c9, LIQUID_REAGENT_1, 5)"""

    print("Dispensing DCDP")
    #time.sleep(10)

def recapMixTBP(cap_height: int):
    """c9.goto_xy_safe(vial_clamp)
    c9.move_axis(c9.Z_AXIS, cap_height)
    cap(c9)
    c9.open_clamp()
    c9.move_z(150)
    #alternating_mix(c9, 5, 80, 4)"""

    print("Recapping and mixing in TBP")
    #time.sleep(10)

def sonicate(dur: int):
    # ! Method will likely have to be updated to make sure the arm regrabs the vial at the end of sonication
    """sonicate(c9, duration = dur)"""
    print("Beginning sonication")
    time.sleep(dur)
    print("Sonication over")

def dry():
    # ! Method will likely have to be updated to make sure the arm regrabs the vial before drying
    ''' c9.goto_safe(g_sponge_adjacent)
    c9.goto(g_sponge)
    alternating_mix(c9, 5, 5, 4)
    c9.goto(g_sponge_adjacent)
    c9.move_z(85)
    alternating_mix(c9, 5, 40, 4) '''
    print("Drying")
    time.sleep(10)

def uncap_vial_post_sonic():
    """c9.goto_safe(vial_clamp)
    c9.close_clamp()
    c9.open_gripper()
    load_mold(c9)
    c9.goto_safe(vial_clamp)
    c9.close_gripper()
    uncap(c9)"""
    print("Uncapping vial")
    time.sleep(0.5)

def recap_vial():
    """c9.goto_xy_safe(vial_clamp)
    c9.move_axis(c9.Z_AXIS, cap_height)
    cap(c9)
    c9.open_gripper()
    c9.goto_safe(home)"""

    print("Recapping vial")
    time.sleep(0.5)

def let_vial_go():
    time.sleep(5)
    print("Vial has been let go of")

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
    
    
def prompt_front():
    """linear_slide_go_right()
#     try:
#         recorder.start() # Try/finally method seems to block, not used
#         c9.delay(60)
#     finally:
#         recorder.stop()
    
    recorder.start()
    c9.delay(80)
    recorder.stop()

    time.sleep(0.2)
    disarm_heater(2)
    linear_slide_go_left()"""

    print("Linear slide going right and waiting for front")
    time.sleep(20)
    print("Prompt started linear slide back to the left")

def place_vial_in_safe():
    print("Placing vial in safe area")