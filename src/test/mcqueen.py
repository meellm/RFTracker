import RPi.GPIO as GPIO  # type: ignore
import os
import sys
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from lib.Vehicle import Vehicle
from lib.Gyroscope import Gyroscope
from lib.BluetoothModule import Bluetooth
from lib.PIDController import PIDController

bluetooth_input = ""

gyro                    = Gyroscope()
vehicle                 = Vehicle(pwm_freq = 2000, left_pwm_pin = 18, left_tyres = [26, 25], right_pwm_pin = 19, right_tyres = [23, 24])
bluetooth_module        = Bluetooth(bluetooth_port = 4, server_address = "XX:XX:XX:XX:XX:XX")

turn_pid                = PIDController(Kp = 0.2, Ki = 0.0, Kd = 0.1, target = 0)
straight_pid            = PIDController(Kp = 1.0, Ki = 0.1, Kd = 0, target = 0)

def setup():
    bluetooth_module.start_server()
    bluetooth_handler = threading.Thread(target = bluetooth_handler_thread, daemon = True)
    bluetooth_handler.start()
    gyro.calibrate(300)
    vehicle.adjust_parameters(gyro=gyro, PID_TURN=turn_pid, PID_STRAIGHT=straight_pid, base_speed = 90, base_speed_turn= 50)
def loop():
    global bluetooth_input
    n = 0
    while True:
        if bluetooth_input:
            vehicle.stop()
            match bluetooth_input:
                case "W":
                    print("FORWARD")
                    vehicle.move(1, True)
                case "A":
                    print("LEFT")
                    gyro.calibrate(250)
                    vehicle.turn(60)
                case "D":
                    print("RIGHT")
                    gyro.calibrate(250)
                    vehicle.turn(-60)
                case "S":
                    print("BACKWARD")
                    vehicle.move(1, False)
                case _:
                    print("INVALID INPUT")
                    vehicle.stop()

            bluetooth_input = None

def bluetooth_handler_thread():
    global bluetooth_input
    while True:
        data = bluetooth_module.receive_data()
        if data:
            bluetooth_input = data
        time.sleep(0.5)

if __name__ == "__main__":
    setup()
    loop()
