"""
Implementation for Aman Kansal's optimal energy allocation 
algorithm, as presented in
Power Managemenet in Energy Harvesting Sensor Networks,
ACM Transactions on Embedded Computing Systems, 2007

-----------------
Input:
    - initial battery value (so we can compute final value)
    - energy harvested in each slot up to the horizon
    - power consumption in active mode (can be TX/RX power)
    - min and max energy consumption allowed per slot
    - storage efficiency factor

Output:
    - energy allocation for each slot up to the horizon
    - battery value in each slot up to the horizon

Changed the algorithm slightly:
    - the original does the update (seems to) at the end
    of a slot; we run it at the start
"""
import eh_constants as ehct

class Kansal():
    """Represents an instance of Kansal's algorithm.

    Maintains the energy allocation and can update
    on a per-slot basis.
    
    Run allocate at the start of a cycle, then in each slot
    run update to correct prediction errors.
    """
    
    def eh_coef(self, slot_idx, eh):
        """Computes kansal's coefficient for a dark slot
        
        Parameters:
        slot_idx    -- index of slot in eh
        eh          -- full list of eh values

        Returns     -- slot coefficient, see paper
        """
        return ehct.pc/float(self.eta) + eh[slot_idx]*(1 - 1/self.eta)

    @staticmethod
    def e_to_dc(val):
        """Convert energy to duty cycle.

        This considers that emax is 100%.
        """
        return float(val)/ehct.emax

    @staticmethod
    def dc_to_e(val):
        """Convert duty cycle to energy.

        This considers that emax is 100% duty cycle
        """
        return ehct.emax*val

    
    def __init__(self, eta, slots_per_cycle, t_slot):
        """
        Parameters:
        eta -- efficiency of battery storage
        """
        self.allocation = [0 for i in xrange(slots_per_cycle)]
        self.allocated = 0
        self.eta = eta
        self.t_slot = t_slot

    def allocate(self, eh_pred, b0):
        """Kansal optimal

        Returns    -- energy allocation in each slot
        """
        # convert EH to power
        self.eh = [float(eh)/self.t_slot for eh in eh_pred]
        total_eh = sum([i*self.t_slot for i in self.eh])
        self.allocated = 0
        sunny_slots = []
        dark_slots = []
        # 1. separate sunny from dark slots
        for idx, e in enumerate(self.eh):
            if e >= ehct.pc:
                sunny_slots.append(idx)
                self.allocation[idx] = ehct.dmax
                self.allocated += Kansal.dc_to_e(ehct.dmax)
            else:
                dark_slots.append(idx)
                self.allocation[idx] = ehct.dmin
                self.allocated += Kansal.dc_to_e(ehct.dmin)
        # 2. how much energy have we allocated
        excess = total_eh - self.allocated
        if excess > 0 and len(dark_slots) > 0:
            # underallocated, increase dark slots
            dark_slots.sort(key=lambda x: self.eh_coef(x, self.eh))
            # assign full dmax to as many slots as possible
            available_for = int(excess/Kansal.dc_to_e(ehct.dmax))
            if available_for > len(dark_slots):
                available_for = len(dark_slots)
            for i in xrange(available_for):
                self.allocation[dark_slots[i]] = ehct.dmax
                excess -= Kansal.dc_to_e(ehct.dmax)
            # assign remainder
            if excess > 0 and available_for < len(dark_slots):
                _slt = dark_slots[available_for]
                self.allocation[_slt] = ehct.dmin + (excess/self.t_slot)/((-self.eh[_slt] + ehct.pc)/self.eta+self.eh[_slt])
        elif excess < 0 and len(sunny_slots) > 0:
            # overallocated, decrease sun slots evenly
            per_slot = (self.allocated - total_eh)/float(len(sunny_slots))
            for i in sunny_slots:
                self.allocation[i] -= Kansal.e_to_dc(per_slot)
        # done
        return Kansal.dc_to_e(self.allocation[0])

    def update(self, slot_idx, eh_pred, eh_pred_prev, eh_real, prev_battery):
        """Update the allocation to account for the difference
        between observed and estimated harvested energy

        Parameters
        slot_idx        -- index of current slot
        eh_pred         -- eh prediction for the current slot
        eh_pred_prev    -- eh prediction for the previous slot
        eh_real         -- observed eh_value in previous slot
        prev_battery    -- battery value at the start of the slot
        """
        # convert energy to power
        estimated = eh_pred_prev/float(self.t_slot)
        eh_real_p = eh_real/float(self.t_slot)
        # determine excess energy from the previous slot
        if eh_real > ehct.pc:
            excess = estimated - eh_real_p
        else:
            excess = (estimated - eh_real_p)*(1 - self.allocation[slot_idx-1]*(1-1/self.eta))
        if excess == 0: return Kansal.dc_to_e(self.allocation[slot_idx])
        def R(j, delta):
            if self.eh[j] > ehct.pc:
                return ehct.pc * delta
            else:
                return delta*(ehct.pc/self.eta + self.eh[j]*(1-1/self.eta))

        slots = [(idx, val) for idx, val in enumerate(self.eh)]
        if excess > 0:
            # we have consumed less than allowed, increase consumption
            # in remaining slots
            # sort slots based on eh
            slots.sort(key=lambda x: x[0])
            # reduce to d min in as many slots as possible
            for s in slots:
                if s[0] < slot_idx: continue # slot is in the past
                if R(s[0], ehct.dmax - self.allocation[s[0]]) < excess:
                    excess -= R(s[0], ehct.dmax - self.allocation[s[0]])
                    self.allocation[s[0]] = ehct.dmax
                else:
                    # not enough energy to increase to ehct.dmax
                    if self.eh[s[0]] > ehct.pc:
                        self.allocation[s[0]] += excess/ehct.pc
                    else:
                        self.allocation[s[0]] += excess/(ehct.pc/self.eta + self.eh[s[0]]*(1-1/self.eta))
                    break
        else:
            # we have consumed more than allowed, must compensate
            # reduce the consumption in the slots with lowest estimated E
            slots.sort(key=lambda x: x[0], reverse=True)
            for s in slots:
                if s[0] < slot_idx or self.allocation[s[0]] <= ehct.dmin: continue
                if R(s[0], ehct.dmin - self.allocation[s[0]]) > excess:
                    excess -= R(s[0], ehct.dmin - self.allocation[s[0]])
                    self.allocation[s[0]] = ehct.dmin
                else:
                    # not enough energy to increase to ehct.dmin
                    if self.eh[s[0]] > ehct.pc:
                        self.allocation[s[0]] += excess/ehct.pc
                    else:
                        self.allocation[s[0]] += excess/(ehct.pc/self.eta + self.eh[s[0]]*(1-1/self.eta))
                    break
        # return the allocation for this current slot
        return Kansal.dc_to_e(self.allocation[slot_idx])
                
    def convert_to_e(self):
        e_alloc = []
        for dc in self.allocation:
            e_alloc.append(Kansal.dc_to_e(dc))
        return e_alloc
