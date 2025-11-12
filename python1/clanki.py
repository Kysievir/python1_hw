import argparse
import shlex
import math
import random
from datetime import date, timedelta
from tabulate import tabulate
import textwrap

# Example deck
example_deck = {
  1: {
    "front": "January",
    "back": "Januar",
    "is_new": True
  },
  2: {
    "front": "February",
    "back": "Februar",
    "is_new": True
  },
  3: {
    "front": "March",
    "back": "Marz",
    "is_new": True
  },
  4: {
    "front": "April",
    "back": "April",
    "is_new": True
  },
  5: {
    "front": "May",
    "back": "Mai",
    "is_new": True
  },
  6: {
    "front": "June",
    "back": "Juni",
    "is_new": True
  },
  7: {
    "front": "July",
    "back": "Juli",
    "is_new": True
  },
  8: {
    "front": "August",
    "back": "August",
    "is_new": True
  },
  9: {
    "front": "September",
    "back": "September",
    "is_new": True
  },
  10: {
    "front": "October",
    "back": "Oktober",
    "is_new": True
  },
  11: {
    "front": "November",
    "back": "November",
    "is_new": True
  },
  12: {
    "front": "December",
    "back": "Dezember",
    "is_new": True
  }
}

# utils.py

## A wrapper to always follow each input()
## This is to avoid "dangling" while loops when checking invalid inputs but
## the user exits to Home or Setting instead.
def process_input(state, verify=None):
  """
  The input processor

  This replaces input() to let the user go to Home, Setting, 
  or a deck anywhere in the program. 

  Attributes
    state: The application's state
    verify: A function to check the validity of input and ask the user to try again.
            If None, this function only checks for menu commands.
  """

  is_valid = False
  while not is_valid:
    # Removing leading and trailing whitespaces
    user_input = input("\n> ").strip()  

    if user_input:  # shlex.split() cannot accept None.
      # Split the input for argparse.
      # Shlex can, eg, make "my_deck" and my_deck equivalent.
      input_as_shell = shlex.split(user_input)  
      
      user_args = menu_parser.parse_known_args(input_as_shell)[0]
      arg_dict = vars(user_args)
      if arg_dict.get("quit"):
        quit()
      elif arg_dict.get("home"):
        return home(state)
      elif arg_dict.get("setting"):
        return setting(state)
      elif arg_dict.get("deck"):
        # This returns to Home if the deck is invalid.
        return deck(state, arg_dict.get("deck"))  
    
    if verify:
      # verify should also print some message if invalid.
      is_valid = verify(user_input)
    else:
      is_valid = True  

  return user_input

# Input verifiers
def verify_review(user_input):
  if user_input in {"1", "2", "3", "4"}:
    return True
  else:
    print("Invalid input. Please enter 1, 2, 3, or 4.")
    return False

# A3: Card review scheduling

def in_session_scheduler(state, session_grade, deck_name, card_id):
  if session_grade == 1:
    # Card is considered "new" (True) inside session, requiring at least Easy to pass,
    # if the user presses Again for it.
    state["session"][card_id] = True 
   
  # TODO: This simplistic pass condition should be replaced with something later.
  # Anki has "learning"/"relearning" steps.

  pass_if_new = state["session"][card_id] and (session_grade > 2)
  pass_if_old = (not state["session"][card_id]) and (session_grade > 1)

  if pass_if_new or pass_if_old:
    current_deck = state["decks"][deck_name]

    card = current_deck["cards"][card_id]
    if card.get("last_review_date") is None:
      next_s, next_d, next_interv = fsrs_init(session_grade, 
                                              state["setting"]["fsrs_desired_R"],
                                              state["setting"]["fsrs"])
    else:
      next_s, next_d, next_interv = \
        fsrs((state["date"] - card["last_review_date"]).days,
              session_grade,
              card["stability"],
              card["difficulty"],
              state["setting"]["fsrs_desired_R"],
              state["setting"]["fsrs"])
    
    card["stability"] = next_s
    card["difficulty"] = next_d
    # TODO: Isn't next_interv int already?
    card["due_date"] = state["date"] + timedelta(days=math.ceil(next_interv))
    # TODO: This should be constantly updated, not just at Home.
    card["last_review_date"] = state["date"]  
    card["is_new"] = False

    # This can become one line if deck is a class.
    current_deck["dued_cards"].remove(card_id)
    current_deck["due"] -= 1

    state["session"].pop(card_id) 

# This runs every time (in Home) state["date"] has changed.
# TODO: See how Anki does this differently.
def select_dued_cards(state, cards_daily_limit):
  for current_deck in state["decks"].values():
    # Get all cards dued today
    dued_cards = []
    for card_id in current_deck["cards"]:
      if len(dued_cards) == cards_daily_limit:
        break

      # Ignore new cards for now.
      if current_deck["cards"][card_id].get("due_date") is None:
        continue

      if current_deck["cards"][card_id].get("due_date") <= state["date"]:
        dued_cards.append(card_id)
    
    # These are modified as each card is reviewed.
    current_deck["dued_cards"] = dued_cards
    current_deck["due"] = len(dued_cards)

def select_new_cards(state, new_cards_per_day):
  for current_deck in state["decks"].values():
    new_card_count = 0
    new_cards = []
    for card_id in current_deck["cards"]:
      if current_deck["cards"][card_id]["is_new"]:
        new_cards.append(card_id)
        new_card_count += 1
        if new_card_count == new_cards_per_day:
          break
    
    current_deck["dued_cards"] = current_deck["dued_cards"] + new_cards
    current_deck["due"] = len(current_deck["dued_cards"])


# state["session"] stores a list of cards to be reviewed and its is_new 
# property. If a card is answered Again it becomes new.
def init_session(state, deck_name):
  current_deck = state["decks"][deck_name]
  for card_id in current_deck["dued_cards"]:
    state["session"][card_id] = current_deck["cards"][card_id]["is_new"]


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

def schedule(state):
  select_dued_cards(state, state["setting"]["cards_daily_limit"])
  select_new_cards(state, state["setting"]["new_cards_per_day"])

  
# 1. Home
menu_parser = argparse.ArgumentParser(prog="Menu")
menu_parser.add_argument("-H", "--home", action="store_true")
menu_parser.add_argument("-q", "--quit", action="store_true")
menu_parser.add_argument("-s", "--setting", action="store_true")

# These are not be callable outside Home.
home_parser = argparse.ArgumentParser(prog="Home")
home_parser.add_argument("-d", "--deck", type=str)
home_parser.add_argument("-rm", "--remove", type=str)
home_parser.add_argument("-f", "--forward-day", type=int)

## ASCII art with font Standard as generated by https://patorjk.com/...
logo = textwrap.dedent("""   ____ _       _    _ 
  / ___| |_ __ | | _(_)
 | |   | | '_ \| |/ / |
 | |___| | | | |   <| |
  \____|_|_| |_|_|\_\_|
                       """)

def home(state):
  state["session"] = {}

  today = date.today() + timedelta(days=state["forwarded_days"])
  if (state.get("date") is None) or (state.get("date") != today):
    state["date"] = today
    schedule(state)

  deck_list = [[deck_name, len(deck["cards"]), deck["due"]] 
               for deck_name, deck in state["decks"].items()]

  deck_table = tabulate(deck_list, headers=["Deck", "Total", "Due"])

  welcome_msg = textwrap.dedent(f"""
  Welcome to Clnki (v0.0.1), a minimal spaced repetition system.
  Home | Today is {state["date"]}. Here are the available decks:
  {deck_table}
  Options:
    (Callable anywhere)
      -H, --Home: Return to Home.
      -s, --setting: Open settings.
      -q, --quit: Quit Clnki.
    (Callable only in Home)
      -d my_deck, --deck my_deck: View or create a deck.
      -rm my_deck, --remove my_deck: Remove a deck.
      -f 1, --forward-day 1: Forward date by a number of days.""")

  # TODO: Less wordy home_msg after the first time.
  home_msg = logo + welcome_msg
  print(home_msg)

  user_input = process_input(state)
  if user_input is None:
    user_input = ""
  input_as_shell = shlex.split(user_input)
  user_args = home_parser.parse_known_args(input_as_shell)[0]
  arg_dict = vars(user_args)

  if arg_dict.get("deck"):
    return deck(state, arg_dict.get("deck"))
  elif arg_dict.get("remove"):
    return remove(state, arg_dict.get("remove"))
  elif arg_dict.get("forward_day"):
    return forward_day(state, arg_dict.get("forward_day"))
  
  print("Invalid input. Reloading Home.")
  home(state)

# 1.5 Forward_day
def forward_day(state, days):
  state["forwarded_days"] += days
  home(state)

# 2. Setting
default_fsrs = [0.212, 1.2931, 2.3065, 8.2956, 6.4133,  
                0.8334, 3.0194, 0.001, 1.8722, 0.1666, 
                0.796, 1.4835, 0.0614, 0.2629, 1.6483, 
                0.6014, 1.8729, 0.5425, 0.0912, 0.0658,
                0.1542]

default_setting_vals = {"fsrs": default_fsrs,
                        "fsrs_desired_R": 0.9,
                        "new_cards_per_day": 4,
                        "cards_daily_limit": 25
                        }

# TODO: Invalid argument type must be caught with try-catch.
setting_parser = argparse.ArgumentParser(prog="Settings")
setting_parser.add_argument("--fsrs", type=float, nargs=17)
setting_parser.add_argument("--fsrs-desired-R", type=float)
setting_parser.add_argument("--new-cards-per-day", type=int)
setting_parser.add_argument("--cards-daily-limit", type=int)
setting_parser.add_argument("--default", action="store_true")

def setting(state):
  state["session"] = {}
  setting_vals = state["setting"]

  # TODO: In addition to card daily limit, there should also be expected session time limit.
  
  setting_values_msg = textwrap.dedent(f"""Current settings:
  fsrs: {setting_vals.get("fsrs")}
  fsrs-desired-R: {setting_vals.get("fsrs_desired_R")}
  new-cards-per-day: {setting_vals.get("new_cards_per_day")}
  cards-daily-limit: {setting_vals.get("cards_daily_limit")}
  """)
  # Should this be tabulated for readability?
  setting_options_msg = textwrap.dedent("""Options:
    --fsrs \{a list of 21 floats\}: The 21 canonical FSRS parameters.
    --fsrs-desired-R 0.9: Target probability of recall (R) when the card is scheduled for review.
                          The card is removed from the review session once its R after
                          one day exceeds this value.
    --new-cards-per-day 5: The number of new cards to be scheduled for review per day.
    --cards-daily-limit 25: The maximum number of cards to be reviewed per day.
    --default: Revert all settings to default.
  """)
  print(setting_values_msg + "\n" + setting_options_msg)
  user_input = process_input(state)

  # None will actually never be returned to cause any problem with shlex.
  # This is only to assuage the editor's typechecker.
  if user_input is None:
    user_input = ""

  input_as_shell = shlex.split(user_input)
  user_args = setting_parser.parse_known_args(input_as_shell)[0]
  arg_dict = vars(user_args)

  is_state_changed = False

  if arg_dict.get("fsrs"):
    fsrs_vals = arg_dict.get("fsrs")
    if True:  # TODO: FSRS parameter validity check
      setting_vals["fsrs"] = fsrs_vals
      is_state_changed = True
    else:
      print("Invalid input. FSRS parameter conditions not satisfied.")

  if arg_dict.get("fsrs_desired_R"):
    fsrs_desired_R = arg_dict.get("fsrs_desired_R")

    if fsrs_desired_R > 0 and fsrs_desired_R < 1:
      setting_vals["fsrs_desired_R"] = fsrs_desired_R
      is_state_changed = True
    else:
      print("Invalid input. fsrs-desired-R must be between 0 and 1.")   

  if arg_dict.get("new_cards_per_day"):
    new_cards_per_day = arg_dict.get("new_cards_per_day")

    if new_cards_per_day > 0:
      setting_vals["new_cards_per_day"] = new_cards_per_day
      is_state_changed = True
    else:
      print("Invalid input. new-cards-per-day must be positive.")

  if arg_dict.get("cards_daily_limit"):
    cards_daily_limit = arg_dict.get("cards_daily_limit")

    if cards_daily_limit > 0:
      setting_vals["cards_daily_limit"] = arg_dict.get("cards_daily_limit")
      is_state_changed = True
    else:
      print("Invalid input. cards-daily-limit must be positive")

  if arg_dict.get("default"):
    setting_vals = default_setting_vals.copy()  # TODO: Is .copy() really necessary?
    is_state_changed = True
  
  if is_state_changed:
    schedule(state)
    print("Settings updated. The review schedule may have changed.")
  else:
    print("No setting has been updated.")
  
  print("Returning to Home.")
  home(state)

# 3. Deck
deck_parser = argparse.ArgumentParser(prog="Deck")
deck_parser.add_argument("-r", "--review", action="store_true")
deck_parser.add_argument("-b", "--browse", action="store_true")

def deck(state, deck_name: str):
  state["session"] = {}
  
  if deck_name not in state["decks"]:
    return add_deck(state, deck_name)
  
  current_deck = state["decks"].get(deck_name)

  deck_msg = textwrap.dedent(f"""Deck: {deck_name}
  Total: {len(current_deck['cards'])}
  Dued today: {current_deck['due']}
  """) 
  deck_options_msg = textwrap.dedent("""Options:
      -r, --review: Review dued cards.
      -b, --browse: Browse cards arranged by card_id (order at creation).
  """)
  print(deck_msg + deck_options_msg)
  user_input = process_input(state)
  if user_input is None:
    user_input = ""
  input_as_shell = shlex.split(user_input)
  user_args = deck_parser.parse_known_args(input_as_shell)[0]
  arg_dict = vars(user_args)

  if arg_dict.get("review"):
    return review_deck(state, deck_name)
  
  if arg_dict.get("browse"):
    return browse_deck(state, deck_name)
  
  print("Invalid input.")
  deck(state, deck_name)

add_deck_parser = argparse.ArgumentParser(prog="Add_deck")
add_deck_parser.add_argument("-e", "--exit", action="store_true")
add_deck_parser.add_argument("-f", "--finish", action="store_true")

def add_deck(state, deck_name):
  print(f"Creating a deck with title \"{deck_name}\"")
  print("Please add all the cards in this session. Decks currently cannot be edited.")
  print(textwrap.dedent("""Options:
      -e, --exit: Abort
      -f, --finish: Finish deck creation, discarding the current card.
  """))
  
  new_deck = {}
  card_id = 1
  while True:
    # Inputting the front
    print(f"Card {card_id}" + "\n" + "Front:")
    user_input = process_input(state)
    
    if user_input is None:
      user_input = ""
    input_as_shell = shlex.split(user_input)
    user_args = add_deck_parser.parse_known_args(input_as_shell)[0]
    arg_dict = vars(user_args)

    if arg_dict.get("exit"):
      print("Deck creation aborted. Returning to Home.")
      return home(state)
    
    if arg_dict.get("finish"):
      state["decks"][deck_name] = {}
      state["decks"][deck_name]["cards"] = new_deck
      print(f"Deck \"{deck_name}\" created with {card_id - 1} cards.")
      schedule(state)
      return home(state)
    
    new_card = {"front": user_input}

    # Inputting the back
    print("Back:")
    user_input = process_input(state)
    
    if user_input is None:
      user_input = ""
    input_as_shell = shlex.split(user_input)
    user_args = add_deck_parser.parse_known_args(input_as_shell)[0]
    arg_dict = vars(user_args)

    if arg_dict.get("exit"):
      print("Deck creation aborted. Returning to Home.")
      return home(state)
    
    if arg_dict.get("finish"):
      state["decks"][deck_name] = {}
      state["decks"][deck_name]["cards"] = new_deck
      print(f"Deck \"{deck_name}\" created with {card_id - 1} cards.")
      schedule(state)
      return home(state)
    
    new_card["back"] = user_input
    new_card["is_new"] = True
    new_deck[card_id] = new_card
    card_id += 1

   
def browse_deck(state, deck_name):
  # TODO: You can delete the card here.
  # TODO: How to get on-click input?
  current_deck = state["decks"][deck_name]["cards"]
  for card_id in current_deck:
    print(f"Card {card_id}" + "\n" + "Front:")
    print(current_deck[card_id]["front"])
    print("Back:" + "\n" + current_deck[card_id]["back"] + "\n")

  deck(state, deck_name)

def review_deck(state, deck_name):
  # TODO: check if deck exists
  current_deck = state["decks"][deck_name]

  init_session(state, deck_name)  # Or session = ...?
  while len(state["session"]) > 0:
    card_id = random.choice(list(state["session"]))
    review_card(state, deck_name, card_id)

  print(f"Review for deck {deck_name} finished. Returning to Home.")
  home(state)

def review_card(state, deck_name, card_id):
  # TODO: You can edit the card here.
  # TODO: There should be a command to exit review and return to the deck view.

  decks = state["decks"]
  if decks.get(deck_name) and decks[deck_name]["cards"].get(card_id):
    current_card = decks[deck_name]["cards"].get(card_id)

    print(f"Review in session | Cards remaining: {len(state['session'])}")
    
    print(current_card.get("front"))
    process_input(state)  # The input is for user's reference only and doesn't matter.
    
    print("Back:\n" + current_card.get("back"))
    print("Again (1) | Hard (2) | Easy (3) | Very Easy (4)")
    session_grade = int(process_input(state, verify_review))

    in_session_scheduler(state, session_grade, deck_name, card_id)

    return

# 4. Remove
def remove(state, deck_name):
  decks = state["decks"]
  if decks.get(deck_name):
    print(textwrap.dedent(f"Are you sure you want to delete deck {deck_name} \
    with all its {len(decks[deck_name]['cards'])} cards? (Y/N)"))
    user_input = process_input(state)

    if user_input == "Y":
      decks.pop(deck_name)
      print(f"Deck {deck_name} is removed.")
    elif user_input == "N":
      print("Removal cancelled.")
    else:
      print("Invalid input. Removal cancelled.")

  home(state)


if __name__ == "__main__":
  
  # TODO: Initialize state
  state = {}
  state["forwarded_days"] = 0
  state["decks"] = {}
  state["setting"] = default_setting_vals.copy()
  state["decks"]["German months"] = {}
  state["decks"]["German months"]["cards"] = example_deck
  state["session"] = {}

  home(state)
