from clnki.deck import Deck
from datetime import date

def schedule_daily(decks: list[Deck], today: date, cards_daily_limit: int, new_cards_per_day: int):
    # 1. Select due cards first
    for deck in decks.values():
        due_cards = []
        for card_id in deck.cards:
            if len(due_cards) == cards_daily_limit:
                break
      
        # Ignore new cards for now
        if deck.cards[card_id].get("due_date") is None:
            continue
      
        if deck.cards[card_id].get("due_date") <= today:
            due_cards.append(card_id)

    # Add new cards
    for deck in decks.values():
        new_card_count = 0
        new_cards = []
        for card_id in deck.cards:
            if deck.cards[card_id]["is_new"]:
                new_cards.append(card_id)
                new_card_count += 1
            if new_card_count == new_cards_per_day:
                break

    deck.update_due(due_cards + new_cards)