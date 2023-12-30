from suggestion import Suggestion
import logging


class Player:
    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.card_count = None
        self.weapons = set()
        self.rooms = set()
        self.suspects = set()
        self.does_not_have_suspects = set()
        self.does_not_have_rooms = set()
        self.does_not_have_weapons = set()
        self.answered_suggestions = []
        self.made_suggestion_with_no_answer = []

    def add_card(self, card):
        if self.card_count == len(self.all_known_cards()):
            return  # avoid debug log spam
        if card in self.game.WEAPONS:
            self.weapons.add(card)
        elif card in self.game.ROOMS:
            self.rooms.add(card)
        elif card in self.game.SUSPECTS:
            self.suspects.add(card)
        else:
            raise Exception("invalid card: " + card)

        for other_player in self.game.players:
            if self != other_player:
                other_player.does_not_have_card(card)

        all_known = self.all_known_cards()
        if len(all_known) >= self.card_count:
            for other_card in self.game.all_cards():
                if other_card not in all_known:
                    logging.debug(
                        f"hit card count and inferring {self.name} does not have {other_card}"
                    )
                    self.does_not_have_card(other_card)

    def is_unknown_card(self, card):
        return (
            card not in self.all_known_cards()
            and card not in self.all_known_does_not_have_cards()
        )

    def all_suggestions_with_no_answer_cards(self):
        ret = set()
        for suggestion in self.made_suggestion_with_no_answer:
            ret.add(suggestion.room)
            ret.add(suggestion.weapon)
            ret.add(suggestion.suspect)
        return ret

    def all_known_cards(self):
        return self.weapons | self.rooms | self.suspects

    def all_known_does_not_have_cards(self):
        return (
            self.does_not_have_weapons
            | self.does_not_have_rooms
            | self.does_not_have_suspects
        )

    def review_suggestions_for_inferrable_cards(self):
        # if player responses to guess:         A B C
        # and player does not respond to guess: Z B C
        # we have recorded that player does not
        # have B or C & now can infer that player has 'A'
        does_not_have_cards = self.all_known_does_not_have_cards()
        for suggestion in [
            suggestion
            for suggestion in self.answered_suggestions
            if not suggestion.solved
        ]:
            if (
                suggestion.weapon in does_not_have_cards
                and suggestion.suspect in does_not_have_cards
            ):
                logging.debug(
                    f"inferring from suggestion that {self.name} has card {suggestion.room}"
                )
                self.add_card(suggestion.room)
                suggestion.solved = True
            elif (
                suggestion.room in does_not_have_cards
                and suggestion.suspect in does_not_have_cards
            ):
                logging.debug(
                    f"inferring from suggestion that {self.name} has card {suggestion.weapon}"
                )
                self.add_card(suggestion.weapon)
                suggestion.solved = True
            elif (
                suggestion.weapon in does_not_have_cards
                and suggestion.room in does_not_have_cards
            ):
                logging.debug(
                    f"inferring from suggestion that {self.name} has card {suggestion.suspect}"
                )
                self.add_card(suggestion.suspect)
                suggestion.solved = True

    def check_number_of_remaining_against_number_of_unknown(self):
        # e.g. if player has 1 card left, and there is only one card the player could have, add that card
        remaining_unknown = (
            self.game.all_cards()
            - self.all_known_cards()
            - self.all_known_does_not_have_cards()
        )
        if len(remaining_unknown) > 0 and len(remaining_unknown) == (
            self.card_count - len(self.all_known_cards())
        ):
            logging.debug(f"{self.name} could only have cards: {remaining_unknown}")
            for card in remaining_unknown:
                self.add_card(card)

    def does_not_have_card(self, card):
        if card in self.game.WEAPONS:
            self.does_not_have_weapons.add(card)
        elif card in self.game.ROOMS:
            self.does_not_have_rooms.add(card)
        elif card in self.game.SUSPECTS:
            self.does_not_have_suspects.add(card)

    def does_not_have_suggestion(self, suggestion):
        self.does_not_have_card(suggestion.suspect)
        self.does_not_have_card(suggestion.weapon)
        self.does_not_have_card(suggestion.room)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        else:
            return False
