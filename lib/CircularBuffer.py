class CircularBuffer:
    def __init__(self, capacity):
        self.buffer = [None] * capacity
        self.capacity = capacity
        self.head = 0
        self.size = 0

    def add(self, value):
        self.buffer[self.head] = value
        self.head = (self.head + 1) % self.capacity
        if self.size < self.capacity:
            self.size += 1

    def get(self, index):
        if not (index >= self.size):
            _index = (((self.head - self.size) % self.capacity) + index) % self.capacity
            return self.buffer[_index]
        else:
            return None

    def get_last(self):
        if self.size > 0:
            return self.buffer[(self.head - 1) % self.capacity]
        else:
            return None

    def get_all(self):
        if self.size > 0:
            start = (self.head - self.size) % self.capacity
            return [self.buffer[(start + i) % self.capacity] for i in range(self.size)]
        else:
            return []

    def reset(self):
        for i in range(self.capacity):
            self.buffer[i] = None
        self.head = 0
        self.size = 0
