import eh_constants as ehct
class Buchli():
    def __init__(self, epsilon, slots_per_cycle):
        self.Bcap = ehct.bmax - ehct.bmin
        self.slots = slots_per_cycle
        self.alloc = [0 for i in xrange(self.slots)]
        self.epsilon = epsilon
        self.eh_pred = None

    def allocate(self, eh_pred, B0):
        self.eh_pred = eh_pred
        # compute envelope
        env_l = [sum(eh_pred[:i]) for i in xrange(self.slots)]
        env_u = [i+self.Bcap for i in env_l]
        # initialise f as avg between lower and upper
        f = [(env_l[i]+env_u[i])/2 for i in xrange(self.slots)]
        f[0] = self.Bcap/2.0
        f[-1] = self.Bcap/2.0 + env_l[-1]  # for energy-neutral operation
        # adjust f until reaches optimum
        while True:
            diff_max = 0
            temp = (f[-1] - env_l[-1] + f[1])/2
            temp = max(min(f[0], self.Bcap), 0)
            if abs(f[0] - temp) > diff_max: diff_max = abs(f[0] - temp)
            f[0] = temp
            for t in xrange(1, len(eh_pred)-1):
                temp = (f[t-1] + f[t+1])/2
                temp = max(min(temp, env_u[t]), env_l[t])
                if abs(f[t]-temp) > diff_max: diff_max = abs(f[t]-temp)
                f[t] = temp
            temp = f[0] + env_l[-1]
            if abs(f[-1] - temp) > diff_max: diff_max = abs(f[-1] - temp)
            f[-1] = temp
            if diff_max < self.epsilon: break
        self.alloc = [f[t+1]-f[t] for t in xrange(len(f)-1)]
        self.batt_pred = [env_u[t] - f[t] for t in xrange(self.slots)]
        return self.alloc[0]

    def update(self, slot_idx, eh_pred, eh_pred_prev, eh_obs, batt_start):
        eh_cycle_from_now = self.eh_pred[slot_idx:] + self.eh_pred[:slot_idx]
        return self.allocate(eh_cycle_from_now, batt_start)
