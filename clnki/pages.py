from clnki.base import Page, App, Navigate
from clnki.schedule import schedule_daily
from clnki.deck import Deck, from_json_date_handling, to_json_date_handling
import argparse
import shlex
import json
from tabulate import tabulate
from datetime import date, timedelta
import time

class HomePage(Page):

    __parser = argparse.ArgumentParser(prog="Home", exit_on_error=False)
    __parser.add_argument("-d", "--deck", type=str)
    __parser.add_argument("-rm", "--remove", type=str)
    __parser.add_argument("-f", "--forward-day", type=int)

    logo = """   
 ____ _        _    _ 
/ ___| |_ __  | | _(_)
| |   | | '_ \| |/ / |
| |___| | | | |   <| |
\____|_|_| |_|_|\_\_|"""

    def __init__(self, app: App):
        super().__init__(app)

    def on_mount(self):
        with open(self.app.settings_path, 'r', encoding='utf-8') as f:
            # TODO: Have a default in case the file is empty.
            self.app.settings = json.load(f)
        
        with open(self.app.decks_path, 'r', encoding='utf-8') as f:
            decks_json = json.load(f)
        
        from_json_date_handling(decks_json)
        for deck_name, cards in decks_json.items():
            self.app.decks[deck_name] = Deck(cards)
        
        today = date.today() + timedelta(days=self.app.forwarded_days)
        if (getattr(self.app, "today", None) is None) or (self.app.today != today):
            self.app.today = today
            schedule_daily(self.app.decks, 
                           today, 
                           self.app.settings["cards_daily_limit"],
                           self.app.settings["new_cards_per_day"])

    def render(self):
        deck_list = [[deck_name, len(deck.cards), deck.num_due] 
                     for deck_name, deck in self.app.decks.items()]

        deck_table = tabulate(deck_list, headers=["Deck", "Total", "Due"])

        welcome_msg = f"""
Welcome to Clnki (v0.0.1), a minimal spaced repetition system.
Home | Today is {self.app.today}. Here are the available decks:
{deck_table}
Options:
    (Callable anywhere)
    -H, --Home: Return to Home.
    -s, --setting: Open settings.
    -q, --quit: Quit Clnki.
    (Callable only in Home)
    -d my_deck, --deck my_deck: View or create a deck.
    -rm my_deck, --remove my_deck: Remove a deck.
    -f 1, --forward-day 1: Forward date by a number of days."""

        # TODO: Less wordy home_msg after the first time.
        home_msg = self.logo + welcome_msg
        print(home_msg)

    def next_page(self):
        user_input = input("\n> ")
        args = self.argparser(user_input.strip())
        if args is not None:
            if args.deck:
                return self.app.pages["deck"], {"deck_name": args.deck}
            elif args.remove:
                return self.app.pages["remove"], {"deck_name": args.remove}
            elif args.forward_day:
                self.app.forward_days(args.forward_day)
                return self.app.pages["home"], {}
        
        print("Invalid input. Reloading Home.")
        time.sleep(2)
        return self.app.pages["home"], {}

    @Page.global_parser
    def argparser(self, raw_input: str):
        if raw_input is None:
            raw_input = ""
        input_as_shell = shlex.split(raw_input)

        try: 
            args = self.__parser.parse_known_args(input_as_shell)[0]
        except argparse.ArgumentError:
            args = None

        return args


class SettingsPage(Page):

    __parser = argparse.ArgumentParser(prog="Settings", exit_on_error=False)
    __parser.add_argument("--fsrs", type=float, nargs=17)
    __parser.add_argument("--fsrs-desired-R", type=float)
    __parser.add_argument("--new-cards-per-day", type=int)
    __parser.add_argument("--cards-daily-limit", type=int)
    __parser.add_argument("--default", action="store_true")

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


    def __init__(self, app: App):
        super().__init__(app)
    
    def render(self):
        setting_values_msg = f"""
Current settings:
  fsrs: {self.app.settings.get("fsrs")}
  fsrs-desired-R: {self.app.settings.get("fsrs_desired_R")}
  new-cards-per-day: {self.app.settings.get("new_cards_per_day")}
  cards-daily-limit: {self.app.settings.get("cards_daily_limit")}"""
        
        # Should this be tabulated for readability?
        setting_options_msg = """
Options:
    --fsrs \{a list of 21 floats\}: The 21 canonical FSRS parameters.
    --fsrs-desired-R 0.9: Target probability of recall (R) when the card is scheduled for review.
                          The card is removed from the review session once its R after
                          one day exceeds this value.
    --new-cards-per-day 5: The number of new cards to be scheduled for review per day.
    --cards-daily-limit 25: The maximum number of cards to be reviewed per day.
    --default: Revert all settings to default."""

        print(setting_values_msg + "\n" + setting_options_msg)
    
    def next_page(self):
        user_input = input("\n> ")
        args = self.argparser(user_input.strip())

        is_state_changed = False

        if args.fsrs:
            fsrs_vals = args.fsrs
            if True:  # TODO: FSRS parameter validity check
                self.app.settings["fsrs"] = fsrs_vals
                is_state_changed = True
            else:
                print("Invalid input. FSRS parameter conditions not satisfied.")

        if args.fsrs_desired_R:
            fsrs_desired_R = args.fsrs_desired_R

            if fsrs_desired_R > 0 and fsrs_desired_R < 1:
                self.app.settings["fsrs_desired_R"] = fsrs_desired_R
                is_state_changed = True
            else:
                print("Invalid input. fsrs-desired-R must be between 0 and 1.")   

        if args.new_cards_per_day:
            new_cards_per_day = args.new_cards_per_day

            if new_cards_per_day > 0:
                self.app.settings["new_cards_per_day"] = new_cards_per_day
                is_state_changed = True
            else:
                print("Invalid input. new-cards-per-day must be positive.")

        if args.cards_daily_limit:
            cards_daily_limit = args.cards_daily_limit

            if cards_daily_limit > 0:
                self.app.settings["cards_daily_limit"] = cards_daily_limit
                is_state_changed = True
            else:
                print("Invalid input. cards-daily-limit must be positive")

        if args.default:
            setting_vals = self.default_setting_vals.copy() 
            is_state_changed = True
  
        if is_state_changed:
            schedule_daily(self.app.decks, 
                           date.today(), 
                           self.app.settings["cards_daily_limit"],
                           self.app.settings["new_cards_per_day"])
            print("Settings updated. The review schedule may have changed.")
        else:
            print("No setting has been updated.")
        
        print("Returning to home")
        time.sleep(2)
        return self.app.pages["home"], {}
    
    @Page.global_parser
    def argparser(self):
        if raw_input is None:
            raw_input = ""
        input_as_shell = shlex.split(raw_input)

        try: 
            args = self.__parser.parse_known_args(input_as_shell)[0]
        except argparse.ArgumentError:
            args = None

        return args


class RemoveDeckPage(Page):
    def __init__(self, app: App):
        super().__init__(app)
    
    def on_mount(self, deck_name):
        if self.app.decks.get(deck_name):
            self.deck = deck_name
        else:
            print("The deck does not exist. Returning to home.")
            time.sleep(2)
            raise Navigate(self.app.pages["home"])
    
    def render(self):
        print(f"Are you sure you want to delete deck {self.deck} \
with all its {len(self.app.decks[self.deck]['cards'])} cards? (Y/N)")

    def next_page(self):
        user_input = input("\n> ")
        self.argparser(user_input.strip())

        if user_input == "Y":
            self.app.decks.pop(self.deck)
            print(f"Deck {self.deck} is removed.")
        elif user_input == "N":
            print("Removal cancelled.")
        else:
            print("Invalid input. Removal cancelled.")
        
        return self.app.pages["home"], {}
