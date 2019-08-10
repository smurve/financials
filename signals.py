from statsutils import MovingStats

class BandSignal:
    def __init__(self, major_stats_width, minor_stats_width, history, 
                 std_excess=1.0, drop_from_high = .05, rise_from_low = .05):
        """
        Create a signal recommender
        params: 
        moving_stats_width: number of element to keep in moving stats
        history: history to initialize the stats
        std_excess: factor to apply to std of the differences wr moving average to arrive
            at a threshold for kicking off the watch phase
        down_threshold: ratio of downturn from recent maximum difference to kick off the 'SELL' phase
        up_threshold: ratio of upturn from recent minimum difference to kick off the 'BUY' phase
        
        Example: With a current std of the differences of 2.5 and std_excess of 1.2, the algorithm
        would start watching out for the SELL signal, when the current difference (=the head) is above 
        1.2 * 2.5 = 3.0. Let's assume the head continues upwards until 4 before it loses momentum.
        With a drop_from_high of 0.1 (10% down from the highest difference from the moving average),
        the SELL signal will kick off once the head crosses the (1 - 0.1) * 4.0 = 3.6 mark.
        downwards.
        """
        self.init_stats(major_stats_width, minor_stats_width, history)
        self.values = []
        self.avgs = []
        self.stds = []
        self.diffs = []
        self.heads = []
        self.u_w = []
        self.l_w = []
        self.std_excess = std_excess
        self.current_phase = 0
        self.current_low = 0
        self.current_high = 0
        self.drop_from_high = drop_from_high
        self.rise_from_low = rise_from_low
        
    def init_stats(self, maj_sw, min_sw, history):
        self.stats = MovingStats(maxlen=maj_sw, history = None)
        self.major_diffstats = MovingStats(maxlen = maj_sw, history = None)
        self.minor_diffstats = MovingStats(maxlen = min_sw, history = None)
        for v in history:
            self.stats.push(v)
            m, _ = self.stats.stats()
            self.major_diffstats.push(v - m)
            self.minor_diffstats.push(v - m)
            
            
        
    def next_value(self, value, verbose=False):
        """ 
        processes the next value of the chard
        returns a recommendation: one of 'BUY', 'HOLD', or 'SELL' and an array of time series:
        [value, mean, head, upper_watch, lower_watch] since inception of the signal
        """
        self.values.append(value)
        self.stats.push(value)
        mean, std = self.stats.stats()
        self.avgs.append(mean)
        self.stds.append(std)
        
        diff = value - mean
        self.diffs.append(diff)
        self.major_diffstats.push(diff)
        self.minor_diffstats.push(diff)
        if verbose:
            print("value %s, mean %s, diff %s" % (value, mean, diff))
        
        # From here on, we're only looking at the differences from the moving averages
        _, diff_std = self.major_diffstats.stats()
        upper_watch = diff_std * self.std_excess
        lower_watch = -upper_watch
        self.u_w.append(upper_watch)
        self.l_w.append(lower_watch)
        
        if verbose:
            print("upper %s, lower %s" % (upper_watch, lower_watch))

        head, _ = self.minor_diffstats.stats()
        self.heads.append(head)
        package = [value, mean, head, upper_watch, lower_watch]
        if self.current_phase == 0:
            if head > upper_watch:
                self.current_phase = -1 # sell on next downturn
                if verbose: 
                    print ("%s) Sell watch" % t)
            elif head < lower_watch:
                self.current_phase = 1 # buy on next upturn
                if verbose:
                    print ("%s) Buy watch" % t)
                    
        elif self.current_phase == -1:
            if head > self.current_high:                
                self.current_high = head
            if head < self.current_high * (1 - self.drop_from_high):
                self.current_phase = 2
                return 'SELL', package 

        elif self.current_phase == 1:
            if head < self.current_low:
                self.current_low = head
            if head > self.current_low * (1 - self.rise_from_low):
                self.current_phase = 2
                return 'BUY', package

        elif self.current_phase == 2:
            if head < upper_watch and head > lower_watch:
                self.current_phase = 0
                self.current_high = 0
                self.current_low = 0           
            
        return 'HOLD', package
