from clnki.base import App, Page, ExitApp, Navigate
from clnki.pages import HomePage, SettingsPage, RemoveDeckPage
from clnki.deck_pages import DeckPage, CardReviewPage, NewDeckPage, BrowseDeckPage
from clnki.deck import to_json_date_handling
from os import PathLike
import argparse
import shlex
import json

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


class Clnki(App):

    __parser = argparse.ArgumentParser(prog="Menu", exit_on_error=False)
    __parser.add_argument("-H", "--home", action="store_true")
    __parser.add_argument("-q", "--quit", action="store_true")
    __parser.add_argument("-s", "--settings", action="store_true")

    def __init__(self, decks_path: str | PathLike, settings_path: str | PathLike):
        """
        Args:
            decks_path: path to json holding all decks
            settings_path: path to json holding settings
        """
        super().__init__()
        pages_dict = {
            "home": HomePage(self),
            "settings": SettingsPage(self),
            "remove_deck": RemoveDeckPage(self),
            "deck": DeckPage(self),
            "card_review": CardReviewPage(self),
            "new_deck": NewDeckPage(self),
            "browse_deck": BrowseDeckPage(self)
        }
        self.pages.update(pages_dict)
        self.page = self.pages["home"]

        self.decks_path = decks_path
        self.settings_path = settings_path
        self.forwarded_days = 0

        self.decks = {}
        self.settings = default_setting_vals
    
    def on_quit(self):
        # 1. Save decks
        decks_dict = {deck_name: deck.cards for deck_name, deck in self.decks.items()}
        to_json_date_handling(decks_dict)
        with open(self.decks_path, 'w', encoding='utf-8') as f:
            json.dump(decks_dict, f, indent=4)
        
        # 2. Save settings
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4)
    

    def global_parser(self, raw_input: str):
        if raw_input is None:
            raw_input = ""
        input_as_shell = shlex.split(raw_input)

        try:
            args = self.__parser.parse_known_args(input_as_shell)[0]
        except argparse.ArgumentError:
            pass

        if args.quit:
            raise ExitApp
        elif args.home:
            raise Navigate(self.pages["home"])
        elif args.settings:
            raise Navigate(self.pages["settings"])
    
    def forward_days(self, days: int):
        pass


if __name__ == "__main__":
    clnki = Clnki("clnki\data\decks.json", "clnki\data\settings.json")
    clnki.run()