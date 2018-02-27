import eh_constants as ehct

class Gorlatova():
    """
    Implements the progressive filling algorithm of Gorlatova et al.
    """

    def __init__(self, slots_per_cycle):
        self.slots = slots_per_cycle
        self.alloc = [0 for i in xrange(self.slots)]
        self.delta = 0.0086     # 8.6mJ, according to paper
        self.eh_pred = None

    def check_validity(self, crt_alloc, cycle_eh, B0, test_i, i):
        """
        Check the constraints for the full cycle.
        The energy consumption is crt_alloc,
        except at slot i, where it is test_i.

        Note: I think this will not yield good results because 
        if there's a failure in a prior slot that cannot be redeemed,
        no further increases will be possible.
        """
        B_crt = B0
        for s in xrange(len(cycle_eh)): # The final cycle might be shorter
            if s != i:
                B_crt = B_crt + cycle_eh[s] - crt_alloc[s]
            else:
                B_crt = B_crt + cycle_eh[s] - test_i
            if B_crt < ehct.bmin: # or B_crt > ehct.bmax:
                #print "Error"
                return False
        if B_crt < B0:
            #print "Offset"
            return False
        #print "OK"
        return True

    def allocate(self, eh_pred, B0):
        """
        The PF algorithm is static, doesn't have error correction,
        so everything happens on the first slot of the cycle.
        """
        remaining = set(range(len(eh_pred)))
        self.alloc = [0 for i in xrange(len(eh_pred))]
        while len(remaining) > 0:
            to_remove = set()
            for i in remaining:
                test_i = self.alloc[i] + self.delta
                if self.check_validity(self.alloc, eh_pred, B0, test_i, i):
                    self.alloc[i] = test_i
                else:
                    to_remove.add(i)
            remaining -= to_remove
        return self.alloc[0]

    def update(self, slot_idx, eh_pred, eh_pred_prev, eh_obs, batt_start):
        # The algorithm doesn't provide error correction,
        # so just return the existing allocation.
        return self.alloc[slot_idx]
