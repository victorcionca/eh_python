"""
This class builds forecast models based on EWMA filter.
The predictor assumes time is divided in slots and there
is a cycle.

The cycle has @num_slots slots.

The @alpha parameter is used to tweak the filter:
  - large values will increase the predictor's reliance
  on the past
  - small values will make the predictor quickly react
  to changes (alpha = 0 predicts only based on past slot)

Simulations show an alpha ~= 0.25 gives best results
(minimizes RMSE)

Paremeters:
  @num_slots - number of slots in the cycle
  @alpha     - tweaking parameter
"""
class Predictor:
  def __init__(self, num_slots, alpha):
    self.num_slots = num_slots
    self.slots = []
    self.alpha = alpha
    self.crt_slot = 0
    self.ready = False

  def add_value(self, value):
    if len(self.slots) < self.num_slots:
      self.slots.append(value)
      #print "Added slot", self.crt_slot, ":", value
    else:
      val = (1 - self.alpha) * self.slots[self.crt_slot] + self.alpha * value
      #print "Update slot", self.crt_slot, "with value", value, "=>", self.slots[self.crt_slot], "to", val
      self.slots[self.crt_slot] = val
      self.ready = True
    self.crt_slot = (self.crt_slot + 1) % self.num_slots

  def predict(self, slot):
    return self.slots[slot]

  def predict_cycle(self):
    return self.slots

  """
  This determines the energy prediction for a precise
  timeframe (as opposed to a slot)
  """
  def predict_precise(self, t0, t1, slot_length):
    cycle_length = self.num_slots * slot_length
    pos0 = float(t0 % cycle_length)
    slot0 = int(pos0 / slot_length)
    pos1 = float(t1 % cycle_length)
    slot1 = int(pos1 / slot_length)
    e_cons = 0
    if slot0 == slot1:
      e_cons = (pos1 - pos0) * self.predict(slot0)
    else:
      slot = slot0
      if slot0 == self.num_slots - 1:
        e_cons = (cycle_length - pos0) * self.predict(slot0)
      else:
        e_cons = ((slot0 + 1)*slot_length - pos0) * self.predict(slot0)
      slot = (slot + 1) % self.num_slots
      while slot != slot1:
        e_cons += self.predict(slot)
        slot = (slot + 1) % self.num_slots
      e_cons += (pos1 - slot*slot_length) * self.predict(slot)
    return e_cons
 


if __name__ == '__main__':
  from harvester import Harvester
  from time import sleep
  import random
  
  """
  Test the predictor to see if the energy generated 
  is well predicted
  """
  cycle_length = 24*3600 # 1 day cycle
  exp_length = 10* cycle_length
  slot_size = 60*10 # 10 minute slots

  num_slots = exp_length / slot_size
  slots_per_cycle = cycle_length / slot_size
  slots = []
  prediction = [0 for i in range(0,cycle_length/slot_size)]
  h = Harvester(cycle_length)
  p = Predictor(cycle_length / slot_size, 0.24)
  random.seed()
  for i in range(0, num_slots):
    e_val = h.get_energy(i*slot_size, (i+1)*slot_size)
    e_val += 0.05*random.randint(-10,10)*e_val
    slots.append(e_val)
    p.add_value(e_val)
    prediction.append(p.predict(i % slots_per_cycle))
    #sleep(0.5)
  diffs = []
  for i in range(slots_per_cycle, num_slots):
    err = slots[i] - prediction[i]
    diffs.append(err)

  import matplotlib.pyplot as plt
  plt.figure()
  plt.plot(slots)
  plt.title("Generated")
  plt.figure()
  plt.plot(prediction)
  plt.title("Predicted")
  plt.figure()
  plt.plot(diffs)
  plt.title("Errors")
  plt.show()
