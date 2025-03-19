import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from lib.Gyroscope import Gyroscope

gyro = Gyroscope()

def setup():
    gyro.calibrate(500)

def loop():
    while True:
        print(gyro.get_data())
        time.sleep(1)

if __name__ == "__main__":
    setup()
    loop()
