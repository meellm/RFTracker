import RPi.GPIO as GPIO  # type: ignore

import os
import sys
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from lib.Vehicle import Vehicle
from lib.Gyroscope import Gyroscope
from lib.SDRModule import SDRModule
from lib.BluetoothModule import Bluetooth
from lib.PIDController import PIDController
from lib.CircularBuffer import CircularBuffer

# Constant Parameters                                                           # Will be determined manually
MAX_SIGNAL_POWER = 1.0
SIGNAL_POWER_TOLERANCE = 0.96

# System Parameters
dir = True
system_enable = False
first_run_flag = True

bluetooth_input = None
bluetooth_output = None
bluetooth_output_prio = None
bluetooth_send_flag = False
sdr_save_signal_flag = False

# Object Initializations
gyro                = Gyroscope()
signal_buffer       = CircularBuffer(50)
vehicle             = Vehicle(pwm_freq = 2000, left_pwm_pin = 18, left_tyres = [26, 25], right_pwm_pin = 19, right_tyres = [23, 24])
sdr_module          = SDRModule(sample_rate = 2.4e6, center_freq = 433e6, gain = 3, default_sample_number = 5)
bluetooth_module    = Bluetooth(bluetooth_port = 4, server_address = "XX:XX:XX:XX:XX:XX")

turn_pid            = PIDController(Kp = 0.2, Ki = 0, Kd = 0.1, target = 0)
straight_pid        = PIDController(Kp = 1.0, Ki = 0.1, Kd = 0, target = 0)

# Helper functions
def reset_system():
    global system_enable, first_run_flag

    system_enable = False
    first_run_flag = True
    vehicle.stop()

# Setup
def setup():
    # Start Bluetooth Server
    bluetooth_module.start_server()
    # Start Threads
    bluetooth_receive_handler = threading.Thread(target = bluetooth_receive_handler_thread, daemon = True)
    bluetooth_receive_handler.start()
    bluetooth_send_handler = threading.Thread(target = bluetooth_send_handler_thread, daemon = True)
    bluetooth_send_handler.start()
    sdr_receive_signal_handler = threading.Thread(target = sdr_receive_signal_handler_thread, daemon = True)
    sdr_receive_signal_handler.start()
    # Vehicle Setup
    gyro.calibrate(300)
    vehicle.adjust_parameters(gyro=gyro, PID_TURN=turn_pid, PID_STRAIGHT=straight_pid, base_speed = 90, base_speed_turn = 50)

# Infinite While Loop
def loop():
    global system_enable, first_run_flag, sdr_save_signal_flag, dir
    move_time = 1.5
    rotate_angle = 30
    initial_rotate_number = 6
    while True:
        if system_enable:
            if first_run_flag:
                best_angle, best_signal_power = full_scan(initial_rotate_number, move_time)
                if best_angle == 0.0 or best_angle == -180.0:
                    vehicle.turn(360 / initial_rotate_number)
                    if best_angle == 0.0:
                        dir = False
                elif best_angle == -60.0 or best_angle == 120.0:
                    if best_angle == -60.0:
                        dir = False
                elif best_angle == -120.0 or best_angle == 60.0:
                    vehicle.turn(-360 / initial_rotate_number)
                    if best_angle == -120.0:
                        dir = False

                vehicle.move(2, dir)
                vehicle.set_direction(0)

                checkIfArrived(best_signal_power)
                first_run_flag = False
            else:
                best_angle, best_signal_power = half_scan(rotate_angle, move_time)
                gyro.calibrate(250)

                if best_angle == -1 * rotate_angle:
                    pass
                if best_angle == 0.0:
                    vehicle.turn(rotate_angle)
                if best_angle == rotate_angle:
                    vehicle.turn(-1 * rotate_angle)

                vehicle.move(2, dir)
                vehicle.set_direction(0)

                checkIfArrived(best_signal_power)

def full_scan(initial_rotate_number, move_time):
    global sdr_save_signal_flag, dir, bluetooth_output_prio, bluetooth_send_flag
    signal_powers = {}

    for i in range(initial_rotate_number // 2):
        bluetooth_output_prio = "F" + str(i * 60)
        bluetooth_send_flag = True

        vehicle.move(move_time, True)
        sdr_save_signal_flag = True
        while sdr_save_signal_flag:
            pass
        current_signal_power = signal_buffer.get_last()
        if current_signal_power is not None:
            current_direction = vehicle.get_direction()
            signal_powers[current_direction] = current_signal_power
        vehicle.move(move_time, False)

        time.sleep(0.2)

        vehicle.move(move_time, False)
        sdr_save_signal_flag = True
        while sdr_save_signal_flag:
            pass
        current_signal_power = signal_buffer.get_last()
        if current_signal_power is not None:
            current_direction = vehicle.get_direction()
            signal_powers[(current_direction - 180)] = current_signal_power
        vehicle.move(move_time, True)

        gyro.calibrate(250)
        if i != (initial_rotate_number // 2 - 1):
            vehicle.turn(360 / initial_rotate_number)
            time.sleep(0.2)

    sorted_signal_powers = dict(sorted(signal_powers.items(), key = lambda item: item[1], reverse = True))
    best_angle = list(sorted_signal_powers.keys())[0]
    best_signal_power = signal_powers[best_angle]

    return best_angle, best_signal_power

def half_scan(scan_angle, move_time):
    global sdr_save_signal_flag, dir, bluetooth_output_prio, bluetooth_send_flag
    signal_powers = {}
    gyro.calibrate(250)

    bluetooth_output_prio = "H0"
    bluetooth_send_flag = True

    vehicle.move(move_time, dir)
    sdr_save_signal_flag = True
    while sdr_save_signal_flag:
        pass
    current_signal_power = signal_buffer.get_last()
    if current_signal_power is not None:
        current_direction = vehicle.get_direction()
        signal_powers[current_direction] = current_signal_power
    vehicle.move(move_time, (not dir))

    bluetooth_output_prio = "H30"
    bluetooth_send_flag = True

    gyro.calibrate(250)
    vehicle.turn(scan_angle)

    vehicle.move(move_time, dir)
    sdr_save_signal_flag = True
    while sdr_save_signal_flag:
        pass
    current_signal_power = signal_buffer.get_last()
    if current_signal_power is not None:
        current_direction = vehicle.get_direction()
        signal_powers[current_direction] = current_signal_power
    vehicle.move(move_time, (not dir))

    bluetooth_output_prio = "H-30"
    bluetooth_send_flag = True

    gyro.calibrate(250)
    vehicle.turn(-2 * scan_angle)

    time.sleep(0.2)

    vehicle.move(move_time, dir)
    sdr_save_signal_flag = True
    while sdr_save_signal_flag:
        pass
    current_signal_power = signal_buffer.get_last()
    if current_signal_power is not None:
        current_direction = vehicle.get_direction()
        signal_powers[current_direction] = current_signal_power
    vehicle.move(move_time, (not dir))

    sorted_signal_powers = dict(sorted(signal_powers.items(), key = lambda item: item[1], reverse = True))
    best_angle = list(sorted_signal_powers.keys())[0]
    best_signal_power = signal_powers[best_angle]

    return best_angle, best_signal_power

def checkIfArrived(signal_power):
    global system_enable, bluetooth_output_prio, bluetooth_send_flag
    if signal_power > MAX_SIGNAL_POWER - SIGNAL_POWER_TOLERANCE:
        system_enable = False
        bluetooth_output_prio = "C"
        bluetooth_send_flag = True
        vehicle.stop()

def bluetooth_receive_handler_thread():
    global bluetooth_module, bluetooth_input, system_enable
    while True:
        if bluetooth_module.connection_flag:
            data = bluetooth_module.receive_data()
            if data:
                if data == "START":
                    system_enable = True
                elif data == "STOP":
                    reset_system()
        time.sleep(0.1)

def bluetooth_send_handler_thread():
    global bluetooth_module, bluetooth_output_prio, bluetooth_output, bluetooth_send_flag
    while True:
        if bluetooth_module.connection_flag and bluetooth_send_flag:
            if bluetooth_output_prio is not None:
                bluetooth_module.send_data(bluetooth_output_prio)
            elif bluetooth_output is not None:
                bluetooth_module.send_data(bluetooth_output)
            bluetooth_send_flag = False
            bluetooth_output_prio = None
            bluetooth_output = None
        time.sleep(0.15)

def sdr_receive_signal_handler_thread():
    global sdr_save_signal_flag, system_enable, signal_buffer, bluetooth_output, bluetooth_send_flag
    while True:
        if system_enable:
            if sdr_save_signal_flag:
                signal = sdr_module.signal_receive(2560)
                signal_buffer.add(sdr_module.find_signal_power(signal))
                print(signal_buffer.get_last())
                sdr_save_signal_flag = False
                bluetooth_output = "O"
            else:
                signal = sdr_module.signal_receive(1)
                bluetooth_output = "S" + str(signal)
            bluetooth_send_flag = True
            time.sleep(0.1)

if __name__ == "__main__":
    setup()
    loop()
