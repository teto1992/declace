import time


class Stopwatch:
    class Trigger:
        def __init__(self, stopwatch, tag):
            self.tag = tag
            self.stopwatch = stopwatch

        def __enter__(self):
            self.start = time.time()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop = time.time()
            self.stopwatch.data[self.tag] = self.stop - self.start

    def __init__(self, precision):
        self.data = {}
        self.precision = precision

    def trigger(self, tag):
        return Stopwatch.Trigger(self, tag)

    def get(self, tag):
        return round(self.data[tag], self.precision)

    def clear(self):
        self.data = {}
