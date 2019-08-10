import numpy as np
from collections import deque

class MovingStats:
    def __init__(self, maxlen, history=None):
        self.N = maxlen
        self.queue = deque(history or [], maxlen=maxlen)
        self._calc()

    def _calc(self):
        self.std = np.std(self.queue)
        self.mean = np.mean(self.queue)
        
    def push(self, value):
        self.queue.append(value)
        self._calc()

    def stats(self):
        return self.mean, self.std
    
    
