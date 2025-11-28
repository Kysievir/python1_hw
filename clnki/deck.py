from clnki.fsrs import fsrs, fsrs_init
from datetime import date, timedelta, datetime
import math


# No Card class for now so that json.dump is simple.

class Deck:
    def __init__(self, cards_dict):
        self.cards = cards_dict
        self.due_cards = None  # a list of due card_id's
        self.num_due = 0
    
    def update_due(self, cards_list):
        self.due_cards = cards_list
        self.num_due = len(cards_list)
    
    def review(self, card_id, grade, settings):
        """Update FSRS-related attributes of a card and pop it out of due."""
        # TODO: Check if card_id exists.

        card = self.cards[card_id]

        if card.get("last_review_date") is None:
            next_s, next_d, next_interv = fsrs_init(grade, 
                                              settings["fsrs_desired_R"],
                                              settings["fsrs"])
        else:
            next_s, next_d, next_interv = \
                fsrs((date.today() - card["last_review_date"]).days,
                        grade,
                        card["stability"],
                        card["difficulty"],
                        settings["fsrs_desired_R"],
                        settings["fsrs"])
    
        card["stability"] = next_s
        card["difficulty"] = next_d
        # TODO: Isn't next_interv int already?
        card["due_date"] = date.today() + timedelta(days=math.ceil(next_interv))
        # TODO: This should be constantly updated, not just at Home.
        card["last_review_date"] = date.today()
        card["is_new"] = False

        self.due_cards.remove(card_id)
        self.num_due -= 1

def from_json_date_handling(decks_dict):
    for _, cards in decks_dict.items():
        for card_id in cards:
            if (due_date := cards[card_id].get("due_date")):
                cards[card_id]["due_date"] = datetime.strptime(
                    due_date, "%Y-%m-%d").date()
            
            if (due_date := cards[card_id].get("last_review_date")):
                cards[card_id]["last_review_date"] = datetime.strptime(
                    due_date, "%Y-%m-%d").date()

def to_json_date_handling(decks_dict):
    for _, cards in decks_dict.items():
        for card_id in cards:
            if (due_date := cards[card_id].get("due_date")):
                cards[card_id]["due_date"] = due_date.isoformat()
            
            if (last_review_date := cards[card_id].get("last_review_date")):
                cards[card_id]["last_review_date"] = last_review_date.isoformat()


