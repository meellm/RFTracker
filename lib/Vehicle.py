import RPi.GPIO as GPIO  # type: ignore
import time

class Vehicle:
    def __init__(self, pwm_freq, left_pwm_pin, left_tyres, right_pwm_pin, right_tyres, min_duty = 80, stop_time = 0.5, accel_time = 0.5, max_correction = 20):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.pwm_freq = pwm_freq
        self.min_duty = min_duty
        self.stop_time = stop_time
        self.accel_time = accel_time
        self.MAX_CORRECTION = max_correction

        if isinstance(left_tyres, list) and len(left_tyres) == 2:
            self.left_pwm_pin = left_pwm_pin
            GPIO.setup(self.left_pwm_pin, GPIO.OUT)
            self.left_tyres = left_tyres
            for i in self.left_tyres:
                GPIO.setup(i, GPIO.OUT)
            self.left_pwm = GPIO.PWM(self.left_pwm_pin, self.pwm_freq)
            self.left_pwm.start(0)

        if isinstance(right_tyres, list) and len(right_tyres) == 2:
            self.right_pwm_pin = right_pwm_pin
            GPIO.setup(self.right_pwm_pin, GPIO.OUT)
            self.right_tyres = right_tyres
            for i in self.right_tyres:
                GPIO.setup(i, GPIO.OUT)
            self.right_pwm = GPIO.PWM(self.right_pwm_pin, self.pwm_freq)
            self.right_pwm.start(0)

        self.direction = 0
        self.gyro = None
        self.PID_TURN = None
        self.PID_STRAIGHT = None
        self.base_speed = 0
        self.base_speed_turn = 0
        self.current_direction = None

    def adjust_parameters(self, gyro, PID_TURN, PID_STRAIGHT, base_speed, base_speed_turn):
        self.gyro = gyro
        self.PID_TURN = PID_TURN
        self.PID_STRAIGHT = PID_STRAIGHT
        self.base_speed = base_speed
        self.base_speed_turn = base_speed_turn

    def move(self, sec, dir):
        if dir:
            GPIO.output(self.left_tyres[0], GPIO.HIGH)
            GPIO.output(self.right_tyres[0], GPIO.HIGH)
            self.current_direction = 'forward'
        else:
            GPIO.output(self.left_tyres[1], GPIO.HIGH)
            GPIO.output(self.right_tyres[1], GPIO.HIGH)
            self.current_direction = 'backward'
        self.ramp_up(sec)
        self.stop()

    def turn(self, angle, tolerance=2.0):
        if angle == 0:
            return

        if angle > 0:
            GPIO.output(self.left_tyres[0], GPIO.HIGH)
            GPIO.output(self.right_tyres[1], GPIO.HIGH)
        else:
            GPIO.output(self.left_tyres[1], GPIO.HIGH)
            GPIO.output(self.right_tyres[0], GPIO.HIGH)

        if self.gyro is None:
            duty = max(self.min_duty, self.base_speed_turn)
            self.left_pwm.ChangeDutyCycle(duty)
            self.right_pwm.ChangeDutyCycle(duty)
            time.sleep(abs(angle) * 0.01)
        else:
            last_time = time.time()
            current_angle = 0.0
            filtered_velocity = 0.0
            alpha = 0.1

            self.PID_TURN.set_target(angle)
            while abs(angle - current_angle) > tolerance:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time

                angular_velocity = self.gyro.get_data()['z']
                filtered_velocity = alpha * angular_velocity + (1 - alpha) * filtered_velocity

                current_angle += filtered_velocity * dt

                remaining_angle = abs(angle - current_angle)
                if remaining_angle < 30:
                    dynamic_speed = 0.5 * self.base_speed_turn
                else:
                    dynamic_speed = self.base_speed_turn

                correction = self.PID_TURN.control(current=current_angle, previous=(current_angle - filtered_velocity * dt))
                correction = max(-self.MAX_CORRECTION, min(self.MAX_CORRECTION, correction))

                left_speed = dynamic_speed - correction
                right_speed = dynamic_speed + correction
                left_speed, right_speed = self.clamp_speeds(left_speed, right_speed)

                self.left_pwm.ChangeDutyCycle(left_speed)
                self.right_pwm.ChangeDutyCycle(right_speed)
                time.sleep(0.01)

        for i in self.left_tyres:
            GPIO.output(i, GPIO.LOW)
        for i in self.right_tyres:
            GPIO.output(i, GPIO.LOW)
        self.left_pwm.ChangeDutyCycle(0)
        self.right_pwm.ChangeDutyCycle(0)
        self.adjust_angle(angle)

    def stop(self):
        if self.gyro is None:
            for i in self.left_tyres:
                GPIO.output(i, GPIO.LOW)
            for i in self.right_tyres:
                GPIO.output(i, GPIO.LOW)
            self.left_pwm.ChangeDutyCycle(0)
            self.right_pwm.ChangeDutyCycle(0)
        else:
            stop_time = self.stop_time

            start_time = time.time()
            filtered_velocity = 0.0
            alpha = 0.1
            initial_speed = self.base_speed

            while (time.time() - start_time) < stop_time:
                angular_velocity = self.gyro.get_data()['z']
                filtered_velocity = alpha * angular_velocity + (1 - alpha) * filtered_velocity

                if initial_speed * (1.0 - ((time.time() - start_time) / stop_time)) < (self.min_duty + 10):
                    correction = 0
                else:
                    correction = self.PID_STRAIGHT.control(current=filtered_velocity, previous=0.0)
                    correction = max(-self.MAX_CORRECTION, min(self.MAX_CORRECTION, correction))

                elapsed = time.time() - start_time
                frac = 1.0 - (elapsed / stop_time)
                current_speed = initial_speed * (frac if frac > 0 else 0)

                if self.current_direction == 'forward':
                    left_speed = current_speed - correction
                    right_speed = current_speed + correction
                else:
                    left_speed = current_speed + correction
                    right_speed = current_speed - correction

                left_speed, right_speed = self.clamp_speeds(left_speed, right_speed, for_stop=True)
                self.left_pwm.ChangeDutyCycle(left_speed)
                self.right_pwm.ChangeDutyCycle(right_speed)
                time.sleep(0.01)

            for i in self.left_tyres:
                GPIO.output(i, GPIO.LOW)
            for i in self.right_tyres:
                GPIO.output(i, GPIO.LOW)
            self.left_pwm.ChangeDutyCycle(0)
            self.right_pwm.ChangeDutyCycle(0)

    def adjust_direction(self, angle):
        angle = ((angle + 180) % 360) - 180
        diff = angle - self.direction
        diff = ((diff + 180) % 360) - 180
        if abs(diff) > 0.5:
            self.turn(diff)

    def get_direction(self):
        return self.direction

    def set_direction(self, direction):
        self.direction = direction

    def adjust_angle(self, angle):
        self.direction += angle
        self.direction = ((self.direction + 180) % 360) - 180

    def reset(self):
        self.stop()
        self.direction = 0
        if self.gyro is not None:
            self.gyro.calibrate(300)
        if self.PID_TURN is not None:
            self.PID_TURN.reset()
        if self.PID_STRAIGHT is not None:
            self.PID_STRAIGHT.reset()

    def clamp_speeds(self, left_speed, right_speed, for_stop=False):
        if not for_stop:
            if left_speed > 0 and left_speed < self.min_duty:
                left_speed = self.min_duty
            if right_speed > 0 and right_speed < self.min_duty:
                right_speed = self.min_duty

        left_speed = max(0, min(100, left_speed))
        right_speed = max(0, min(100, right_speed))
        return left_speed, right_speed

    def ramp_up(self, drive_time):
        start_time = time.time()
        filtered_velocity = 0.0
        alpha = 0.1

        while True:
            elapsed = time.time() - start_time
            if elapsed > drive_time:
                break

            ramp_factor = min(1.0, elapsed / self.accel_time) if self.accel_time > 0 else 1.0
            current_speed = self.base_speed * ramp_factor

            if self.gyro:
                angular_velocity = self.gyro.get_data()['z']
                filtered_velocity = alpha * angular_velocity + (1 - alpha) * filtered_velocity

                correction = self.PID_STRAIGHT.control(current=filtered_velocity, previous=0.0)
                correction = max(-self.MAX_CORRECTION, min(self.MAX_CORRECTION, correction))

                if self.current_direction == 'forward':
                    left_speed = current_speed - correction
                    right_speed = current_speed + correction
                else:
                    left_speed = current_speed + correction
                    right_speed = current_speed - correction
            else:
                left_speed = current_speed
                right_speed = current_speed

            left_speed, right_speed = self.clamp_speeds(left_speed, right_speed)
            self.left_pwm.ChangeDutyCycle(left_speed)
            self.right_pwm.ChangeDutyCycle(right_speed)
            time.sleep(0.01)
