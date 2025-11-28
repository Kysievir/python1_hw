import math

def forgetting_curve(elapsed_days, s, w):
  decay = -1 * w[20]
  factor = 0.9 ** (1 / decay) - 1
  return math.pow(1 + factor * elapsed_days / s, decay)

def next_interval(s, desired_r, w):
  decay = -1 * w[20]
  factor = 0.9 ** (1 / decay) - 1
  new_interval = s / factor * (math.pow(desired_r, 1 / decay) - 1)
  return max(round(new_interval, 2), 1)

def init_stability(grade, w):  # grade will always be 2 for now.
  return round(max(w[int(grade - 1)], 0.1), 2)

def init_difficulty(grade, w):
  return clamp_difficulty(w[4] - math.exp(w[5] * (grade - 1)) + 1)

def clamp_difficulty(d):
  return min(max(round(d, 2), 10), 1)

def mean_reversion(init, current, w):
  return w[7] * init + (1 - w[7]) * current

def linear_damping(delta_d, d):
  return delta_d * (10 - d) / 9

def next_difficulty(d, grade, w):
  delta_d = -1 * w[6] * (grade - 3)
  next_d = d + linear_damping(delta_d, d)
  return clamp_difficulty(mean_reversion(init_difficulty(3, w), next_d))

def next_recall_stability(d, s, r, grade, w):
  hard_penalty = w[15] if (grade == 2) else 1
  easy_bonus = w[16] if (grade == 4) else 1

  s_inc = 1 + math.exp(w[8]) * (11 - d) * \
          math.pow(s, -w[9]) * (math.exp(w[10] * (1 - r)) - 1) * \
          hard_penalty * easy_bonus
  return round(s * s_inc, 2)

def next_forget_stability(d, s, r, w): 
  s_new = w[11] * math.pow(d, -w[12]) * (math.pow(s + 1, w[13])-1) \
          * math.exp(w[14] * (1 - r))
  return round(min(s_new, s), 2)

# TODO: This function is not used for now.
def next_short_term_stability(s, grade, w):  # Notice that Difficulty doesn't matter.
  s_inc = math.exp(w[17] * (grade - 3 + w[18])) * math.pow(s, -w[19])
  if (grade >= 3):
    s_inc = max(s_inc, 1)
  return round(s * s_inc, 2)


def fsrs(elapsed_days, grade, s, d, desired_r, w):
  """
  The FSRS algorithm.

  Receive a card's S(tability), D(ifficulty) and update them as well as
  return time till next review. Called when a card is popped from a session.

  Attributes:
    grade: 1, 2, 3, 4 for Again, Hard, Easy, Very Easy
    s: Card's stability
    d: Card's difficulty
    w: FSRS parameters
  """
  r = forgetting_curve(elapsed_days, s, w)
  if grade < 2:
    next_s = next_forget_stability(d, s, r, w)
  else:
    next_s = next_recall_stability(d, s, r, grade, w)
    
  next_d = next_difficulty(d, grade, w)
  next_interv = next_interval(s, desired_r, w)
  return next_s, next_d, next_interv

def fsrs_init(grade, desired_r, w):
  s = init_stability(grade, w)
  d = init_difficulty(grade, w)
  next_interv = next_interval(s, desired_r, w)
  return s, d, next_interv
