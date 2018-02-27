"""
Determine the optimum energy consumption,
based on the prediction of harvested solar energy

The algorithm's main goal is to keep battery level
between zero and max. Also, to have Bn=B1

The battery level is considered as energy
We consider a linear energy storage.

"""
class BatterySlot:
  def __init__(self, type, start, size, avg, min, max, wasted, missed, delta_e_full, delta_e_sleep):
    self.type = type  # 'emax', 'ein', 'emin'
    self.start = start
    self.size = size
    self.min = min      # min battery value in slot
    self.max = max      # max battery value in slot
    self.wasted = wasted
    self.missed = missed
    self.delta_e_full = delta_e_full    # amount by which cons can be increased
    self.delta_e_sleep = delta_e_sleep  # amount by which cons can be decreased

  def error(self, delta_b, b_min, b_max):
    #return max(self.wasted + delta_b, self.missed - delta_b)
    wasted = self.max - b_max
    missed = b_min - self.min
    return max(wasted + delta_b, missed - delta_b)

  def error_type(self, delta_b, b_min, b_max):
    wasted = self.max - b_max
    missed = b_min - self.min
    if wasted + delta_b > 0:
      return 'emax'
    if missed - delta_b > 0:
      return 'emin'

  def __repr__(self):
    return "<From %d to %d, %s, min=%.2f, max=%.2f, delta_full=%.2f delta_sleep=%.2f>" % (self.start, self.start + self.size, self.type, self.min, self.max, self.delta_e_full, self.delta_e_sleep)
    #return "<From %d to %d, %s, min=%.2f, max=%.2f, wasted=%f, missed=%f>" % (self.start, self.start + self.size, self.type, self.min, self.max, self.wasted, self.missed)
    #return "From %d to %d, %s, wasted=%.2f, missed=%.2f" % (self.start, self.start + self.size, self.type, self.wasted, self.missed)

  def __str__(self):
    return "From %d to %d, min=%d, max=%d" % (self.start, self.start + self.size, self.min, self.max)

# global variables
#e_cons = [] # list of e_cons slots
"""
e_cons[i] can be:
  - == e_in[i]
  - == e_min, if e_in[i] < e_min
  - == e_max, if e_in[i] > e_max.
batt_slots are consecutive slots where
e_cons[i] is the same.
In each batt_slots[i] we store:
  - avg(batt_slots[i0:i1]
  - min and max
  - total wasted or missed (B > Bmax or B < Bmin)
"""
#batt_slots = []
#batt = []

"""
Builds the next minimum list from the data list
In the next minimum list, every item represents
the minimum value from that position on in the list
"""
def next_minimum_list(data_list):
  l = []
  l.extend(data_list)
  prev_min = l[-1]
  for i in range(len(data_list)-1, -1, -1):
    l[i] = min(l[i], prev_min)
    prev_min = l[i]
  return l

def opposite(type):
  if type == 'emax':
    return 'emin'
  if type == 'emin':
    return 'emax'

"""
Return the list of battery deltas, given the error type.
If err_type is 'emax', return (B(i) - Bmin).
If err_type is 'emin', return (Bmax - B(i)).
"""
def delta_list(batt_slot_list, err_type, bmax, bmin):
  deltas = []
  for b in batt_slot_list:
    if err_type == 'emax':
      deltas.append(b.min - bmin)
    elif err_type == 'emin':
      deltas.append(bmax - b.max)
  return deltas

"""
Tweak the energy consumption in the list to eliminate
the errors

We need to know:
  - the type of the errors that are recovered (emin or emax)
  because we need to know which slots can be modified
  - the maximum error that must be recovered
  - the list
  - the next minimum for every item
  - any previous change that would affect the list
  - minimum and maximum energy consumption possible in a slot.

We need to get out of this:
  - a list of the changes made and the slots where they were made
  - keep track and return the total amount of energy changed, so
  it can be taken into account in the subsequent slots.
"""
def process_slots(slots, max_err, err_type, next_min_list, batt_delta, emin, emax):
  #print next_min_list, len(next_min_list)
  changes = [(0, batt_delta) for i in range(len(slots))]
  idx = 0
  batt_change = batt_delta
  while idx < len(slots) and max_err > 0:
    # change only in ein and opposite slots
    max_energy_delta = None
    if err_type == 'emin':
      max_energy_delta = slots[idx].delta_e_sleep
    elif err_type == 'emax':
      max_energy_delta = slots[idx].delta_e_full
    if slots[idx].type in ['ein', opposite(err_type)]:
      if err_type == 'emin': # overspend
        # battery change reduces the minimum
        change = min(max_err, next_min_list[idx] - batt_change, max_energy_delta)
      elif err_type == 'emax': # waste
        # battery change increases the minimum
        change = min(max_err, batt_change + next_min_list[idx], max_energy_delta)
      max_err -= change
      # store change
      if err_type == 'emin': # overspent energy, decrease consumption
        change = -change
      batt_change -= change
      #print "Slot", idx, "change", change, "acc", batt_change
      # TODO we can apply the battery change right away
      # TODO we need to apply the change only to the slot end value
      # TODO as we apply the change the slot type might change
      changes[idx] = (change, batt_change)
    else:
      changes[idx] = (0, batt_change)
    if slots[idx].type == err_type and max(slots[idx].wasted, slots[idx].missed) > abs(batt_change):
      # we couldn't recover the error in this slot
      # Note: we can use the second expression in the test,
      # as we can't have both
      # wasted and missed in a slot (failure in previous pass)
      print "Error in slot", idx, max(slots[idx].wasted, slots[idx].missed), "couldn't be recovered. Change so far", batt_change
      return None
    idx += 1
  if max_err > 0:
    print "Remaining error:", max_err
    return None
  else:
    while idx < len(slots):
      changes[idx] = (0, batt_change)
      idx += 1
  return (changes, batt_change)


#def schedule(B0, e_in, e_min, e_max, b_min, b_max):
  
def first_pass(B0, e_in, e_min, e_max, b_min, b_max):
  """
  In each slot, set the energy consumption to e_in, if possible.
  If e_in is too low, set ec to e_sleep.
  If e_in is too high, set ec to e_full.
  Calculate the battery values at the end of each slot.
  Based on the slope of those values, split the data
  into battery slots, where the battery is monotonic.

  This pass also checks for some fail conditions.

  B0: initial battery level
  e_in: list of harvested energy values
  e_min: minimum possible energy consumption (all sleep)
  e_max: maximum possible energy consumption (all active)
  b_min, b_max: lower and upper battery levels
  
  returns list of energy consumption slots, battery and battery slots
  """
  batt_slots = []
  batt = [B0]
  e_cons = []

  # statistics in batt_slot[i]
  batt_last = B0        # battery level in previous slot
  batt_min = B0         # minimum level in battery slot
  batt_max = B0         # maximum level in battery slot
  batt_sum = 0          # sum of levels, for average level
  batt_slot_size = 0    # size of battery slot
  batt_wasted = 0       
  batt_missed = 0
  batt_slot_start = 0   # battery slot position in day
  total_e_cons_in_slot = 0

  prev = None
  # First pass:
  # Assign maximum possible energy consumption in each slot
  # While doing this, keep track of battery values
  # TODO: implement first pass fail condition checking
  for slot in e_in:
    crt = None
    crt_e_cons = None
    # determine amount of e_cons in this slot
    if slot >= e_max:
      crt = 'emax'
      crt_e_cons = e_max
    elif slot <= e_min:
      crt = 'emin'
      crt_e_cons = e_min
    else:
      crt = 'ein'
      crt_e_cons = slot
    # if we changed slots, reset statistics
    if crt != prev and prev != None:
      # check fail conditions
      # 1. max waste or overspending larger than battery cap
      #if max(batt_wasted, batt_missed) > (b_max - b_min):
      #  print "Fail max waste/overspend", batt_wasted, batt_missed, (b_max - b_min)
      #  return None
      # 2. energy loss or gain greater than battery cap
      if (batt_max - batt_min) > (b_max - b_min):
        print "Fail loss/gain", batt_max, batt_min, (b_max - b_min)
        #return None
      batt_slots.append(BatterySlot(prev, batt_slot_start, batt_slot_size, float(batt_sum)/batt_slot_size, batt_min, batt_max, batt_wasted, batt_missed, batt_slot_size*e_max - total_e_cons_in_slot, total_e_cons_in_slot - batt_slot_size*e_min))
      batt_min = batt_max = batt_last
      batt_sum = 0
      batt_slot_start += batt_slot_size
      batt_slot_size = 0
      batt_wasted = batt_missed = 0
      total_e_cons_in_slot = 0
    # update battery value
    batt_delta = slot - crt_e_cons
    batt_crt = batt_last + batt_delta
    if batt_crt < b_min:
      if batt_missed < (b_min - batt_crt): # only track the maximum value
        batt_missed = (b_min - batt_crt)
      # the algorithm must keep track of the battery as if there was no min/max
      #batt_crt = b_min
    if batt_crt > b_max:
      if batt_wasted < (batt_crt - b_max): # only track the maximum
        batt_wasted = (batt_crt - b_max)
      # batt_crt = b_max
    # update statistics
    batt_slot_size += 1
    batt_sum += batt_crt
    if batt_crt < batt_min:
      batt_min = batt_crt
    if batt_crt > batt_max:
      batt_max = batt_crt
    # prepare for next slot
    e_cons.append(crt_e_cons)
    total_e_cons_in_slot += crt_e_cons
    batt.append(batt_crt)
    batt_last = batt_crt
    prev = crt

  #Done going through e_in slots. We may have battery data to 
  #append to batt_slots
  if batt_slot_size > 0:
    batt_slots.append(BatterySlot(prev, batt_slot_start, batt_slot_size, float(batt_sum)/batt_slot_size, batt_min, batt_max, batt_wasted, batt_missed, batt_slot_size*e_max - total_e_cons_in_slot, total_e_cons_in_slot - batt_slot_size*e_min))
  
  return (e_cons, batt, batt_slots)


def second_pass(batt_slots, bmin, bmax, emin, emax):
  ###################################################
  # Second pass: eliminate any waste and overspending
  ###################################################

  # TODO: keep track of all the changes
  # TODO: indicate if there is no solution

  # scan the list until there is an error of opposite type
  index = 0             # keep track of position in list
  crt_err_type = None   # to determine changes in error type
  list_start = 0        # for subsequent processing of the list
  max_err = 0
  max_err_index = 0
  batt_delta = 0
  tent_err = 0
  changes = [(0,0) for i in range(len(batt_slots))]
  for idx, b in enumerate(batt_slots):
      if b.wasted != 0 or b.missed != 0:
          print "Batt error in slot %d: %s" % (idx, b)
  while index < len(batt_slots):
    if batt_slots[index].type == 'ein':
      index += 1
      continue
    # include the max_err as a tentative change
    if batt_slots[index].error(batt_delta+tent_err, bmin, bmax) > 1e-6:
      # we have an error
      if crt_err_type == None:
        # it's the first one we encountered
        crt_err_type = batt_slots[index].type
      elif crt_err_type != batt_slots[index].error_type(batt_delta+tent_err, bmin, bmax):
        # found error of opposite type, analyse what we have so far
        print "Slots [%d:%d] max_error = %f at %d" % (list_start, max_err_index, max_err, max_err_index)
        # determine next minimum for [list_start:index]
        next_min_list = next_minimum_list(delta_list(batt_slots[list_start:max_err_index + 1], crt_err_type, bmax, bmin))
        # process list [list_start:max_err_index+1]
        process_rez = process_slots(batt_slots[list_start: max_err_index+1], max_err, crt_err_type, next_min_list, batt_delta, emin, emax)
        if process_rez == None:
          print "Second pass: couldn't recover error"
          return None
        (changes[list_start:max_err_index+1], batt_delta) = process_rez

        # reset statistics
        crt_err_type = batt_slots[index].type
        list_start = max_err_index+1
        index = max_err_index +1
        max_err = 0
        tent_err = 0
        max_err_index = 0
        continue
    # track maximum error and its index
    if batt_slots[index].error(batt_delta, bmin, bmax) > max_err:
      max_err = batt_slots[index].error(batt_delta, bmin, bmax)
      max_err_index = index
      tent_err = max_err
      if crt_err_type == 'emax':
        tent_err = -tent_err
    index += 1
  
  # handle any remaining slots
  if list_start < len(batt_slots) and max_err != 0:
    print "Last slots [%d:%d] max_error = %f at %d" % (list_start, max_err_index, max_err, max_err_index)
    # determine next minimum for [list_start:]
    next_min_list = next_minimum_list(delta_list(batt_slots[list_start:], crt_err_type, bmax, bmin))
    # process list [list_start:]
    process_rez = process_slots(batt_slots[list_start:], max_err, crt_err_type, next_min_list, batt_delta, emin, emax)
    if process_rez == None:
      print "Second pass: couldn't recover error"
      return None
    (changes[list_start:], batt_delta) = process_rez

  # the last batt_delta will modify the offset
  return (changes, batt_delta)


def offset_correction(batt_slots, changes, B0, bmin, bmax):
  """
  Correct the final battery offset.
  Start from the end of the list and apply changes
  until either of the following:
  - delta of the opposite type is lower than remaining offset
  - reach the start of the list.
  Can only apply changes that reduce the offset
  """
  # TODO: what do we return?
  final_changes = [0 for i in range(len(batt_slots))]
  offset = None
  if batt_slots[-1].type == 'emin':
    offset = B0 - (batt_slots[-1].min + changes[-1][1])
  else:
    offset = B0 - (batt_slots[-1].max + changes[-1][1])
  
  # can we reduce the offset in the final slot?
  if offset > 0 and batt_slots[-1].type in ['ein', 'emax']:
    final_changes[-1] = -min(offset, batt_slots[-1].delta_e_sleep + changes[-1][0])
  elif offset < 0 and batt_slots[-1].type in ['ein', 'emin']:
    # negative offset here because delta_e_full > 0
    final_changes[-1] = min(-offset, batt_slots[-1].delta_e_full - changes[-1][0])

  offset += final_changes[-1]
  if abs(offset) < 1e-6:
    # lucky break!
    return final_changes # TODO: what do we return?

  # not so lucky, there is still some offset left
  # min_delta represents the maximum amount of energy that can
  # be corrected from the offset without causing waste or overspending
  min_delta = None
  if batt_slots[-2].type in ['ein', 'emax']:
      end_slot = batt_slots[-2].max + changes[-2][1]
  else:
      end_slot = batt_slots[-2].min + changes[-2][1]
  if offset > 0:
    min_delta = bmax - end_slot
  else:
    min_delta = end_slot - bmin
  
  index = len(batt_slots) - 2
  while index >=0 and min_delta >= abs(offset) and abs(offset) > 0:
    change = 0
    if offset > 0 and batt_slots[index].type in ['ein', 'emax']:
      # reduce energy consumption to reduce offset
      # TODO no need to have min_delta in the following, since we know it's >= offset
      change = -min(offset, batt_slots[index].delta_e_sleep + changes[index][0], min_delta)
    elif offset < 0 and batt_slots[index].type in ['ein', 'emin']:
      # increase energy consumption to reduce offset
      #   negative offset here because delta_e_sleep > 0
      change = min(-offset, batt_slots[index].delta_e_full - changes[index][0], min_delta)
    offset  += change
    final_changes[index] = change
    #print "At", index, min_delta, "Offset =", offset
    index -= 1
    if batt_slots[index].type in ['ein', 'emax']:
      end_slot = batt_slots[index].max + changes[index][1]
    else:
      end_slot = batt_slots[index].min + changes[index][1]
    if offset > 0:
      min_delta = min(bmax - end_slot, min_delta)
    else:
      min_delta = min(end_slot - bmin, min_delta)
    #print "At", index, min_delta, "Offset =", offset
  
  #if abs(offset) > 0:
  #  print "Left with offset", offset, "at index", index
  
  return final_changes
  


def apply_changes(changes, batt_slots, consumption, emin, emax):
  """
  Changes need to be applied in a greedy manner on the
  slots of energy consumption.
  Change as much as possible in every slot, without going
  outside the (emin, emax) limit.

  If we just use an average it might not work properly
  """
  updated_cons = []
  updated_cons.extend(consumption)
  for (idx, ch) in enumerate(changes):
    if ch == 0:
      continue
    b_slot = batt_slots[idx]
    # effect the change on the consumption, distributing evenly
    #per_slot = float(ch)/b_slot.size
    #for i in range(b_slot.start, b_slot.start + b_slot.size):
    #  updated_cons[i] += per_slot
    
    # cannot distribute evenly, especially for constant slots
    for i in range(b_slot.start, b_slot.start + b_slot.size):
      new_e_cons = updated_cons[i] + ch
      # what is the remaining change
      if new_e_cons < emin:
        ch = new_e_cons - emin
        updated_cons[i] = emin
      elif new_e_cons > emax:
        ch = new_e_cons - emax
        updated_cons[i] = emax
      else:
        updated_cons[i] = new_e_cons
        ch = 0
        break # done
    if abs(ch) > 1e-6:
      print "Left with", ch, "in slot", i, "batt slot", idx
      return None # couldn't apply transformation - this shouldn't happen
  return updated_cons   
    
def compute_battery(B0, econs, ein, bmin, bmax, e_min, e_max):
  """
  Given values for harvested and consumed energy,
  determine the battery values
  """
  battery = [B0]
  
  prev = None
  for (i, ein_i) in enumerate(ein):
    delta_e = ein_i - econs[i]
    b_i = battery[-1] + delta_e
    battery.append(b_i)
  return battery

def simple_optimum(B0, bmin, bmax, emin, emax, e_in):
  """
  Run the algorithm
  """
  first_pass_rez = first_pass(B0, e_in, emin, emax, bmin, bmax)
  if first_pass_rez == None:
    print "Failure in first pass"
    return None
  (e_cons, batt, batt_slots) = first_pass_rez
  second_pass_rez = second_pass(batt_slots, bmin, bmax, emin, emax)
  if second_pass_rez == None:
    print "Failure in second pass"
    return None
  (changes, batt_delta) = second_pass_rez
  final_changes = offset_correction(batt_slots, changes, B0, bmin, bmax)
  if len(final_changes) == 0:
    print "Error in offset correction"
    return None
  total_changes = [e[0][0] + e[1] for e in zip(changes, final_changes)]
  new_cons = apply_changes(total_changes, batt_slots, e_cons, emin, emax)
  if new_cons == None:
    print "Error applying changes"
    return None
  new_batt = compute_battery(B0, new_cons, e_in, bmin, bmax, emin, emax)
  return (new_cons, new_batt, batt_slots)

import eh_constants as ehct
class MallecOptimal():
    def __init__(self, slots_per_cycle):
        self.allocation = [0 for i in xrange(slots_per_cycle)]
        self.battery_pred = None
        self.battery_slots = []
        self.current_batt_slot = 0
        self.offset_in_batt_slot = 0
        self.start_batt = None

    def allocate(self, eh_pred, start_batt):
        if self.start_batt == None:
            self.start_batt = start_batt
        self.allocation, self.battery_pred, self.battery_slots = simple_optimum(self.start_batt, ehct.bmin, ehct.bmax, ehct.emin, ehct.emax, eh_pred)
        self.current_batt_slot = 0
        self.offset_in_batt_slot = 0
        return self.allocation[0]

    def update(self, slot_idx, eh_pred, eh_pred_prev, eh_observed, crt_batt):
        """Increase or decrease the energy allocated in the current
        battery slot, accounting for prediction errors
        """
        # how many slots are left in the current battery slot?
        remaining = self.battery_slots[self.current_batt_slot].size - self.offset_in_batt_slot
        # allocate the energy difference in a greedy fashion, avoiding errors
#        excess = crt_batt - self.battery_pred[slot_idx]
#        if abs(excess) > 1e-6:
#            print excess
#        for i in range(slot_idx, slot_idx+remaining):
#            new_e_cons = self.allocation[i]+excess
#            # what is the remaining change
#            if new_e_cons < ehct.emin:
#                excess = new_e_cons - ehct.emin
#                self.allocation[i] = ehct.emin
#            elif new_e_cons > ehct.emax:
#                excess = new_e_cons - ehct.emax
#                self.allocation[i] = ehct.emax
#            else:
#                self.allocation[i] = new_e_cons
#                excess = 0
#                break # done

        per_slot = (crt_batt - self.battery_pred[slot_idx])/float(remaining)
        map(lambda x: x+per_slot, self.allocation[slot_idx:slot_idx+remaining])
        # advance in battery slot
        if self.offset_in_batt_slot == self.battery_slots[self.current_batt_slot].size - 1:
            # next slot
            self.current_batt_slot += 1
            self.offset_in_batt_slot = 0
        else:
            self.offset_in_batt_slot += 1
        return self.allocation[slot_idx]
        
#if __name__ == '__main__':
#  # harvested energy
#  p_in_file = open('power.dat', 'r')
#  e_in = [600*i for i in [float(line.split(',')[1]) for line in p_in_file]]
#  p_in_file.close()
#
#  # constants
#  e_max = 44
#  e_min = 0.21
#  b_min = 0.3
#  b_max = 31.2
#  B0 = 25

