# Python energy harvesting simulation framework

This is a framework for simulating energy harvesting devices and for evaluating
power management algorithms.

Energy harvesting devices are simulated in terms of their energy consumption 
profile.

The framework works with traces of harvested energy.

The following algorithms were implemented:
* Maximum Allowed Energy Consumption (MAllEC)
* kansal: implementation of algorithm from "Power management in energy harvesting sensor networks", Kansal et al, ACM TECS 2007
* buchli: implementation of Periodic Optimal Control algorithm from "Optimal power management with guaranteed minimum energy utilization for solar energy harvesting systems", Buchli et al, DCOSS 2015
* gorlatova: implementation of Progressive Filling algorithm from "Networking low-power energy harvesting devices: Measurements and algorithms", Gorlatova et al, INFOCOM, 2011.


## Components

The algorithm simulation engine is implemented in alg\_tester.py.
* power management algorithms are abstracted with the SimAlg class (see below)
* the EHSimulator class takes an EH trace, loads algorithms, and then for each
  cycle in the trace:
  * runs each algorithm at the start of the cycle
  * for each slot obtains the algorithm's recommended energy consumption
* each algorithm stores the following statistics:
  * recommended energy consumption profile
  * cumulative sum of harvested energy
  * cumulative sum of predicted harvested energy
  * battery profile
  * total waste (wasted EH due to battery full) and overspending (battery goes below min threshold, equiv shutdown) errors
  * minimum and maximum energy consumption.
* the _runsim_ function is a convenient way of executing the simulator
  * returns the processing statistics for all algorithms
* the simulator can run with perfect (oracle) and error-prone energy harvesting prediction; the latter is achieved with an EWMA filter (in predictor.py).

Plotting functions are provided in plotting.py
* this will plot the simulation results with bar charts.

An example of how the simulator can be used to validate a set of algorithms
through a set of EH traces is provided in run\_test.py.


## Adapting power management algorithms for the simulator

Following functionality is required:

### allocate(eh-pred, B0)

This is run at the start of a cycle and performs the initial, static, allocation.

Input:
* eh-pred: predicted EH trace for the cycle
* B0: initial battery level.

Returns:
* the energy allocated for this slot.

### update(slot-idx, eh-pred, eh-pred-prev, eh-obs, batt-start)

This is run at the start of each slot and it's used for correcting errors due
to discrepancies between the observed and predicted EH.

Returns:
* the energy allocated for slot-idx, after error correction.

Input:
* slot-idx: index of the current slot
* eh-pred: EH value that was predicted
* eh-pred-prev: EH value predicted for the previous slot
* eh-obs: observed EH value for this slot (slot-idx)
* batt-start: battery value at the start of the slot (end of prev slot).
