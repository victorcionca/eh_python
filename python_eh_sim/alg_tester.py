"""
This is a simple framework for testing energy allocation algorithms.

It loads up an energy harvested trace, an initial battery level
as well as min and max allowed battery levels.

It runs an algorithm to extract the energy allocation, it then computes
the battery trace and determines if there are any violations.
"""

from time import time
import numpy as np

class EHAlg():
    """Abstract base class for algorithms.
    This is purely indicative since there are no abstract classes in Python
    """
    
    def allocate(self, eh_cycle_pred, start_battery):
        pass

    def update(self, slot_idx, eh_pred_crt, eh_pred_prev, eh_observed_prev, start_batt):
        pass

class SimAlg():
    """For maintaining and running an algorithm in the simulation"""
    def __init__(self, name, alg, B0):
        self.name = name
        self.alg = alg
        self.allocation = []    # allocation for the full eh_trace
        self.harvested = 0      # cumulative sum of harvested energy
        self.predicted = 0      # cumulative sum of predicted harvested energy
        self.battery = [B0]       # complete battery trace
        self.errors = []        # {'idx', 'type':'waste'/'overspent', 'quantity'}
        self.min_e_used = None
        self.zero_e_slots = 0   # number of slots when alg consumed 0
        self.max_e_used = None
        self.slot_count = 0

    def update_metrics(self, e, eh, eh_pred):
        self.allocation.append(e)
        self.harvested += eh
        self.predicted += eh_pred
        self.slot_count += 1
        b = self.battery[-1] + eh - e
        if self.min_e_used == None or e < self.min_e_used:
            self.min_e_used = e
        if self.max_e_used == None or e > self.max_e_used:
            self.max_e_used = e
        if e == 0:
            self.zero_e_slots += 1
        if b < ehct.bmin:
            self.errors.append({'idx':len(self.allocation)-1, 'type':'overspent', 'quantity': ehct.bmin - b})
            b = ehct.bmin
        elif b > ehct.bmax:
            self.errors.append({'idx':len(self.allocation)-1, 'type':'waste', 'quantity': b - ehct.bmax})
            b = ehct.bmax
        self.battery.append(b)

    def allocate(self, eh_pred):
        """Allocate energy for slots up until the finite horizon,
        using the harvesting prediction eh_pred.
        """
        e = self.alg.allocate(eh_pred, self.battery[-1])
        return e

    def update(self, slot_idx, eh_pred, eh_pred_prev, eh_observed):
        """Update an allocation, correcting prediction errors if any.

        Parameters:
        slot_idx      -- current slot index
        eh_pred       -- prediction for the current slot
        eh_pred_prev  -- prediction for the previous slot
        eh_observed   -- observed eh in the previous slot
        """
        e = self.alg.update(slot_idx, eh_pred, eh_pred_prev, eh_observed, self.battery[-1])
        return e

    def pretty_print(self):
        print "Algorithm:", self.name
        print "Total allocated %d vs harvested %d predicted %d. Ratio %2.2f. Emin %.2f Emax %.2f Zero slots %d" % (sum(self.allocation), self.harvested, self.predicted, sum(self.allocation)/float(self.harvested), self.min_e_used, self.max_e_used, self.zero_e_slots)
        print "Battery errors %d total slots %d quantity %d. Waste %d overspent %d. Final %f" % (len(self.errors), self.slot_count, sum([e['quantity'] for e in self.errors]), sum([e['quantity'] for e in self.errors if e['type'] == 'waste']), sum([e['quantity'] for e in self.errors if e['type'] == 'overspent']), self.battery[-1])
        return [sum(self.allocation), self.harvested, sum([e['quantity'] for e in self.errors]), self.battery[-1]]

class EHTrace():
    def __init__(self, trace_file, sampling_interval, slot_length, panel_area, div_factor):
        """
        An EH trace imported from a file.
        The file needs to have on each line: <measurement index, irrad (uW/cm2)>.
        Parameters:
        trace_file          -- EH trace file as above.
        sampling_interval   -- time interval between two consec measurements
        slot_length         -- time slot length for the algorithm
        panel_area          -- size of panel in cm2
        div_factor          -- allows dividing the harvested energy.
        """
        with open(trace_file) as f:
            eh_trace0 = [float(l.split(',')[1]) for l in f if l[0] != ',']
            eh_trace = [sum([eh*panel_area*sampling_interval/(10**6*div_factor) for eh in eh_trace0[i*(slot_length/sampling_interval):(i+1)*(slot_length/sampling_interval)]]) for i in xrange((len(eh_trace0)-1)/(slot_length/sampling_interval))]
            self.trace = eh_trace
        self.sampling_interval = sampling_interval
        self.slot_length = slot_length
        self.slots_per_cycle = 24*3600/self.slot_length
        self.panel_area = panel_area
        self.div_factor = div_factor

    def __len__(self):
        return len(self.trace)

    def __getitem__(self, k):
        return self.trace.__getitem__(k)

import eh_constants as ehct
from predictor import Predictor
class DummyPredictor():
    def __init__(self, trace, slots_per_cycle):
        self.trace = trace
        self.slots_per_cycle = slots_per_cycle
        self.index = 0

    def add_value(self, val):
        pass

    def predict_cycle(self):
        self.index += self.slots_per_cycle
        #print "Using Dummy predictor"
        return self.trace[self.index:self.index+self.slots_per_cycle]

    def predict(self, idx):
        return self.trace[self.index+idx]

class EHSimulator():
    def __init__(self, eh_trace, b0, dummy_predictor=False):
        """
        Parameters:
        eh_trace    -- energy harvesting trace
        b0          -- initial battery value
        dummy_predictor -- True if want to use oracle, false for EWMA
        """
        self.eh_trace=eh_trace
        self.b0=b0
        # TODO comment this next line to use the dummy predictor
        self.dummy_predictor = dummy_predictor
        if not self.dummy_predictor:
            self.predictor = Predictor(self.eh_trace.slots_per_cycle, ehct.pred_alpha)
        self.algorithms = []
        self.runtime = {}
        self.mallec_batt_slots = []

    def add_algorithm(self, name, alg):
        self.algorithms.append(SimAlg(name, alg, self.b0))
        self.runtime[name] = []

    def load_trace(self, trace_file, sampling_interval, panel_area, factor):
        """Load a trace from file, considering:
        trace_file          -- lines are <index,irradiance>, measured in uW/cm^2
        sampling_interval   -- period between readings in the file
        panel_area          -- size of panel to be used in the simulation
        factor              -- factor to divide the trace
        """
        with open(trace_file) as f:
            eh_trace0 = [float(l.split(',')[1]) for l in f if l[0] != ',']
            eh_trace = [sum([eh*panel_area*sampling_interval/(10**6*factor) for eh in eh_trace0[i*(ehct.t_slot/sampling_interval):(i+1)*(ehct.t_slot/sampling_interval)]]) for i in xrange((len(eh_trace0)-1)/(ehct.t_slot/sampling_interval))]
            self.eh_trace = eh_trace

    def run(self):
        """Runs the simulation for the given trace and with the registered
        algorithms.
        Prints the results.
        Returns the results as follows:
            for each algorithm, [allocated, harvested, errors, final]
        """
        num_slots = len(self.eh_trace)
        # TODO uncomment this next to use the dummy predictor
        if self.dummy_predictor:
            self.predictor = DummyPredictor(self.eh_trace, self.eh_trace.slots_per_cycle)
        day = 0
        # first cycle is only for obtaining the prediction, no algorithms run
        for eh in self.eh_trace[:self.eh_trace.slots_per_cycle]:
            self.predictor.add_value(eh)
        # run the algorithms for the remainder of the trace
        for idx, eh in enumerate(self.eh_trace[self.eh_trace.slots_per_cycle:]):
            _idx = idx%self.eh_trace.slots_per_cycle
            if _idx == 0:
                # a new cycle starts
                cycle_pred = self.predictor.predict_cycle()
                #if day > 2: break
                # run the allocation part of algorithms at the start of the cycle
                for a in self.algorithms:
                    start = time()
                    e = a.allocate(cycle_pred)
                    end = time()
                    self.runtime[a.name].append(end-start)
                    if a.name == 'mallec':
                        self.mallec_batt_slots.append(len(a.alg.battery_slots))
                    a.update_metrics(e, eh, self.predictor.predict(_idx))
                day += 1
            else:
                # update the allocation for this slot
                for a in self.algorithms:
                    e = a.update(_idx, self.predictor.predict(_idx), self.predictor.predict(_idx-1), self.eh_trace[idx-1])
                    a.update_metrics(e, eh, self.predictor.predict(_idx))
            # update the predictor with this latest observed EH value
            self.predictor.add_value(eh)
        results = []
        # print the results
        for a in self.algorithms:
            a_res = a.pretty_print()
            results.append(a_res)
        # print runtime statistics
        for alg, timings in self.runtime.items():
            print alg, np.mean(timings), np.std(timings)
        # print battery slot statistics
        print np.mean(self.mallec_batt_slots), np.std(self.mallec_batt_slots)
        return results

def runsim(trace, algorithms, batt_init, with_oracle):
    """
    Runs a simulation for the given algorithms and trace
    Parameters:
    trace       -- Instance of EHTrace
    algorithms  -- List of ('alg_name', alg instance)
    batt_init   -- Initial battery level
    with_oracle -- True/False for oracle/error prediction
    """
    sim = EHSimulator(trace, batt_init, with_oracle)
    #sim.load_trace(trace, 3600, 25, factor)
    for alg_name, alg in algorithms:
        sim.add_algorithm(alg_name, alg)
    rez = sim.run()
    print "-------------------------------------------------------------------"
    return rez



