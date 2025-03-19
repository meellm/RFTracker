class PIDController:
    def __init__(self, Kp, Ki, Kd, target):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.target = target
        self.integral_term = 0
        self.derivative_term = 0
        self.integral_limit = 100

    def control(self, current, previous):
        error = self.target - current
        previous_error = self.target - previous

        self.integral_term = max(-self.integral_limit, min(self.integral_limit, self.integral_term + error))

        self.derivative_term = current - previous

        output = (error * self.Kp) + (self.integral_term * self.Ki) + (-self.derivative_term * self.Kd)

        return output

    def set_target(self, target):
        self.target = target
        self.integral_term = 0

    def reset(self):
        self.integral_term = 0
        self.derivative_term = 0
        self.target = 0
