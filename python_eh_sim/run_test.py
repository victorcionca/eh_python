"""
Function to run the simulator with Optimal, Kansal and Buchli algorithms
and a trace.

Used 10 for epsilon
"""
import _kansal
import _buchli
import gorlatova
import optimised_scheduler_for_energy_neutrality as mallec
import eh_constants as ehct

from alg_tester import EHTrace, runsim

# Trace specification:
# (file, measurement_interval, desired_time_slot, panel_area, div_factor)
traces=[
        ('../datasets/columbia_irr_only_no_gaps.csv',30,600,25,1)
        ('../datasets/724125_rad_only_full_no_gaps.csv',3600,3600,25,100),
        ('../datasets/724699_rad_only_full_no_gaps.csv',3600,3600,25,100),
        ('../datasets/724776_rad_only_full_no_gaps.csv',3600,3600,25,100),
        ('../datasets/725315_rad_only_full_no_gaps.csv',3600,3600,25,100),
        ('../datasets/726830_rad_only_full_no_gaps.csv',3600,3600,25,100),
        ('../datasets/726883_rad_only_full_no_gaps.csv',3600,3600,25,100),
        ('../datasets/726930_rad_only_full_no_gaps.csv',3600,3600,25,100)
        ]

def test_all(with_oracle, pickle_res = False):
    """
    Run all the tests for all the algorithms.

    with_oracle -- True if want to use oracle, False for EWMA
    pickle_res  -- If True will pickle the results.
    """

    results = []
    for f in traces:
        trace = EHTrace(*f)

        algorithms = []
        # Kansal with eta = 1
        algorithms.append(('kansal', _kansal.Kansal(1, trace.slots_per_cycle, trace.slot_length)))
        algorithms.append(('mallec', mallec.MallecOptimal(trace.slots_per_cycle)))
        # Buchli with epsilon = 10
        algorithms.append(('buchli', _buchli.Buchli(10, trace.slots_per_cycle)))
        algorithms.append(('gorlatova', gorlatova.Gorlatova(trace.slots_per_cycle)))

        results.append(runsim(trace, algorithms, ehct.bmax, with_oracle))

    if pickle_res:
        import pickle
        pickle.dump(results, open('comparative_analysis_results.pickle', 'w'))

    return results


