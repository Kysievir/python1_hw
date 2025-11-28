from clnki.base import Page, App, Navigate
from clnki.schedule import schedule_daily
from clnki.deck import Deck
import argparse
import shlex
import json
from datetime import date, timedelta
import time
import random

class DeckPage(Page):

    __parser = argparse.ArgumentParser(prog="Deck", exit_on_error=False)
    __parser.add_argument("-r", "--review", action="store_true")
    __parser.add_argument("-b", "--browse", action="store_true")

    def __init__(self, app: App):
        super().__init__(app)
    
    def on_mount(self, deck_name):
        if self.app.decks.get(deck_name):
            self.deck = deck_name
        else:
            raise Navigate(self.app.pages["new_deck"], deck_name=deck_name)
    
    def render(self):
        current_deck = self.app.decks.get(self.deck)
        deck_msg = f"""Deck: {self.deck}
Total: {len(current_deck.cards)}
Dued today: {current_deck.num_due}
""" 
        deck_options_msg = """Options:
      -r, --review: Review dued cards.
      -b, --browse: Browse cards arranged by card_id (order at creation).
  """
        print(deck_msg + deck_options_msg)

    def next_page(self):
        user_input = input("\n> ")
        args = self.argparser(user_input.strip())

        if args.review:
            return self.app.pages.get("card_review"), {"deck_name": self.deck}
  
        if args.browse:
            return self.app.pages.get("browse_deck"), {"deck_name": self.deck}
  
        print("Invalid input.")
        time.sleep(2)
        return self.app.pages.get("deck"), {"deck_name": self.deck}

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
        

class BrowseDeckPage(Page):
    def __init__(self, app: App):
        super().__init__(app)
    
    def on_mount(self, deck_name):
        self.deck = deck_name
    
    def render(self):
        current_deck = self.app.decks.get(self.deck)
        for card_id in current_deck.cards:
            print(f"Card {card_id}" + "\n" + "Front:")
            print(current_deck.cards[card_id]["front"])
            print("Back:" + "\n" + current_deck.cards[card_id]["back"] + "\n")

    def next_page(self):
        print("Press anything to return: ")
        user_input = input("\n> ")
        self.argparser(user_input.strip())
        
        return self.app.pages["deck"], {"deck_name": self.deck}


class CardReviewPage(Page):
    def __init__(self, app: App):
        super().__init__(app)

    # TODO: Accept card_id as well so that terminal can be cleared.
    def on_mount(self, deck_name: str):
        self.deck = deck_name
        self.init_session()  # TODO: Remove this.
    
    def render(self):
        pass

    def next_page(self):
        while len(self.session) > 0:
            card_id = random.choice(list(self.session.keys()))
            self.review_card(card_id)

        print(f"Review for deck {self.deck} finished. Returning to Home.")
        return self.app.pages["home"], {}
        

    # state["session"] stores a list of cards to be reviewed and its is_new 
    # property. If a card is answered Again it becomes new.
    def init_session(self):
        current_deck = self.app.decks.get(self.deck)
        self.session = {}
        for card_id in current_deck.due_cards:
            self.session[card_id] = current_deck.cards[card_id]["is_new"]

    def review_card(self, card_id):
        # TODO: You can edit the card here.
        # TODO: There should be a command to exit review and return to the deck view.

        current_deck = self.app.decks.get(self.deck)

        if current_deck and current_deck.cards.get(card_id):
            current_card = self.app.decks.get(self.deck).cards.get(card_id)

            print(f"Review in session | Cards remaining: {len(self.session)}")
            
            print(current_card.get("front"))
            user_input = input("\n> ")  # The input is for user's reference only and doesn't matter.
            self.argparser(user_input.strip())
            
            print("Back:\n" + current_card.get("back"))
            print("Again (1) | Hard (2) | Easy (3) | Very Easy (4)")

            is_valid = False
            while not is_valid:

                user_input = input("\n> ")
                self.argparser(user_input.strip())
                user_input = user_input.strip()
                if user_input in {"1", "2", "3", "4"}:
                    is_valid = True
                else:
                    print("Invalid input. Please enter 1, 2, 3, or 4.")

            session_grade = int(user_input)

            self.in_session_scheduler(session_grade, card_id)

        return
    
    def in_session_scheduler(self, session_grade, card_id):
        current_deck = self.app.decks.get(self.deck)  # This a Deck object.

        if session_grade == 1:
            # Card is considered "new" (True) inside session, requiring at least Easy to pass,
            # if the user presses Again for it.
            self.session[card_id] = True 
        
        # TODO: This simplistic pass condition should be replaced with something later.
        # Anki has "learning"/"relearning" steps.

        pass_if_new = self.session[card_id] and (session_grade > 2)
        pass_if_old = (not self.session[card_id]) and (session_grade > 1)

        if pass_if_new or pass_if_old:
            current_deck.review(card_id, session_grade, self.app.settings)

            self.session.pop(card_id) 


class NewDeckPage(Page):

    __parser = argparse.ArgumentParser(prog="Add_deck", exit_on_error=False)
    __parser.add_argument("-e", "--exit", action="store_true")
    __parser.add_argument("-f", "--finish", action="store_true")

    def __init__(self, app: App):
        super().__init__(app)
    
    def on_mount(self, deck_name):
        self.deck = deck_name
    
    def render(self):
        print(f"Creating a deck with title \"{self.deck}\"")
        print("Please add all the cards in this session. Decks currently cannot be edited.")
        print("""Options:
      -e, --exit: Abort
      -f, --finish: Finish deck creation, discarding the current card.""")

    def next_page(self):
        new_deck = {}
        card_id = 1
        while True:
            # Inputting the front
            print(f"Card {card_id}" + "\n" + "Front:")
            user_input = input("\n> ")
            args = self.argparser(user_input.strip())
            if args is not None:
                if args.exit:
                    print("Deck creation aborted. Returning to Home.")
                    return self.app.pages["home"], {}
            
                if args.finish:
                    self.app.decks[self.deck] = Deck(new_deck)
                    print(f"Deck \"{self.deck}\" created with {card_id - 1} cards.")
                    schedule_daily(self.app.decks, 
                           date.today(), 
                           self.app.settings["cards_daily_limit"],
                           self.app.settings["new_cards_per_day"])
                    return self.app.pages["home"], {}
            
            new_card = {"front": user_input}

            # Inputting the back
            print("Back:")
            user_input = input("\n> ")
            args = self.argparser(user_input.strip())
            if args is not None:
                if args.exit:
                    print("Deck creation aborted. Returning to Home.")
                    return self.app.pages["home"], {}
            
                if args.finish:
                    self.app.decks[self.deck] = Deck(new_deck)
                    print(f"Deck \"{self.deck}\" created with {card_id - 1} cards.")
                    schedule_daily(self.app.decks, 
                           date.today(), 
                           self.app.settings["cards_daily_limit"],
                           self.app.settings["new_cards_per_day"])
                    return self.app.pages["home"], {}
            
            new_card["back"] = user_input
            new_card["is_new"] = True
            new_deck[str(card_id)] = new_card  # keys in json must be strings
            card_id += 1
    
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
