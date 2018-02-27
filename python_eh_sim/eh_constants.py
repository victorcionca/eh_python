"""
Constants for Energy Harvesting, to be used by the
algorithms
"""

# slot length
t_slot = 3600    # 60s per slot
# max power consumption
pc = 0.06   # 20mA*3V = 60mW = 0.06
# min and max allowed energy consumption
emin = 3*(0.024*0.050 + 0.000020*(t_slot-0.050)) #1pkt/slot rest spent sleeping
emax = 3*0.024*t_slot   # radio on constantly
# min and max allowed duty cycle
dmin = 0.0016659
dmax = 1
# minimum and maximum battery thresholds
bmin = 16200    # half-way threshold
bmax = 32400    # energy stored in 2AA batteries (3Ah, 3V), in Joules
slots_per_cycle = 24*3600/t_slot  # 24h*60slots/h
# predictor alpha
pred_alpha = 0.25
