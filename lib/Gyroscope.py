from mpu6050 import mpu6050

class Gyroscope:
    def __init__(self):
        self.mpu = mpu6050(0x68)
        self.offset_x = 0
        self.offset_y = 0
        self.offset_z = 0

    def calibrate(self, n):
        x = 0
        y = 0
        z = 0
        for i in range(n):
            x += self.mpu.get_gyro_data()['x']
            y += self.mpu.get_gyro_data()['y']
            z += self.mpu.get_gyro_data()['z']
        self.offset_x = x / n
        self.offset_y = y / n
        self.offset_z = z / n

    def get_data(self):
        data = self.mpu.get_gyro_data()
        data['x'] -= self.offset_x
        data['y'] -= self.offset_y
        data['z'] -= self.offset_z
        return data

    def reset(self):
        self.offset_x = 0
        self.offset_y = 0
        self.offset_z = 0
