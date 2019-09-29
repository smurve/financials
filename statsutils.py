import numpy as np
from collections import deque

class MovingStats:
    def __init__(self, maxlen, history=None):
        self.N = maxlen
        self.queue = deque(history or [], maxlen=maxlen)

    def _calc(self):
        self.std = np.std(self.queue)
        self.mean = np.mean(self.queue)
        
    def push(self, value):
        self.queue.append(value)

    def stats(self):
        if len(self.queue) > 2:
            self._calc()
            return self.mean, self.std
        else:
            return 0., 0.
    
    
# average along the axis using sections of a given length
def avg_over_axis(orig, axis, section):
    shape = np.shape(orig)
    dim_a = shape[axis]
    expanded = np.expand_dims(orig, axis+1)
    new_shape = list(expanded.shape)
    new_shape[axis] = dim_a//section
    new_shape[axis+1] = section

    reshaped = np.reshape(orig, new_shape)
    rolled = np.rollaxis(reshaped, axis+1, 0)
    avg = 0
    for r in rolled:
        avg += r / section
    return avg
    
