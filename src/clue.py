import yaml
import os
import logging

from suggestion import Suggestion
from game import Game
from player import Player
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys


# Set up the logger
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")


def parse_suggestion(game, suggestion_data):
    elements = suggestion_data.split()
    if len(elements) != 4:
        raise Exception("invalid suggestion: " + suggestion_data)

    player_name = elements[0]
    if player_name not in [player.name for player in game.players]:
        raise Exception("invalid player name: " + player_name)

    cards = elements[1:]
    suggestion = Suggestion(player_name)
    for card in cards:
        if card in game.SUSPECTS:
            suggestion.suspect = card
        elif card in game.WEAPONS:
            suggestion.weapon = card
        elif card in game.ROOMS:
            suggestion.room = card
        else:
            raise Exception("invalid card: " + card)

    if (
        suggestion.suspect is None
        or suggestion.weapon is None
        or suggestion.room is None
    ):
        raise Exception(
            f"Invalid suggestion '{suggestion_data}'. Please include one suspect, one weapon, and one room."
        )
    else:
        return suggestion


def process_suggestion(game, suggestion_data):
    suggestion = parse_suggestion(game, suggestion_data["q"])
    logging.debug(f"processing suggestion: {suggestion}")
    answer_data = suggestion_data["a"].split()
    answerer_name = answer_data[0]
    logging.debug(f"suggestion answered by: {answerer_name}")

    if answerer_name == "nobody":
        for player in game.players:
            if player.name != suggestion.player_name:
                player.does_not_have_suggestion(suggestion)
        # the suggester could have all or none of the suggested cards
        # unfortunately you can't infer anything from this
        guesser = game.get_player(suggestion.player_name)
        guesser.made_suggestion_with_no_answer.append(suggestion)
    else:
        answerer = game.get_player(answerer_name)
        if answerer is None:
            raise Exception(f"Player {answerer_name} not found.")
        guesser = game.get_player(suggestion.player_name)
        guesser_index = game.players.index(guesser)
        # get index of player who showed the card
        answerer_index = game.players.index(answerer)

        # get all players between the guesser and the player who showed the card
        if guesser_index != answerer_index:
            if guesser_index < answerer_index:
                players_between = game.players[guesser_index + 1 : answerer_index]
            else:
                players_between = game.players[0:answerer_index]
                players_between += game.players[guesser_index + 1 :]
        else:
            players_between = []
        logging.debug(
            f"players: {[player_between.name for player_between in players_between]} do not have the cards: {suggestion.suspect}, {suggestion.weapon}, {suggestion.room}"
        )

        # record that the players between do not have the cards in the suggestion
        for player_between in players_between:
            player_between.does_not_have_suggestion(suggestion)

        if len(answer_data) > 1:
            logging.debug(
                f"recording that answerer {answerer.name} has card: {answer_data[1]}"
            )
            answerer.add_card(answer_data[1])
        else:
            # record that the player who showed the card has the suggestion
            answerer.answered_suggestions.append(suggestion)

        return suggestion, answerer


def process_reveal(game, reveal):
    player_name, card = reveal["r"].split()
    logging.debug(f"{player_name} has {card}")

    if player_name != "nobody":
        game.get_player(player_name).add_card(card)
    else:
        for player in game.players:
            player.does_not_have_card(card)


def check_for_completed_section(game, gamecards, get_player_cards):
    # if all cards but one are known in a section
    # then we know that card is in the file
    known_cards = []
    for player in game.players:
        known_cards.extend(get_player_cards(player))
        known_cards.extend(game.not_solution_cards)

    remaining_unknown = [card for card in gamecards if card not in known_cards]

    if len(remaining_unknown) == 1:
        # found answer
        for player in game.players:
            player.does_not_have_card(remaining_unknown[0])


def check_for_completed_sections(game):
    check_for_completed_section(game, game.WEAPONS, lambda p: p.weapons)
    check_for_completed_section(game, game.ROOMS, lambda p: p.rooms)
    check_for_completed_section(game, game.SUSPECTS, lambda p: p.suspects)


def check_for_infer_section(game, section_cards, section_solution):
    # here bob either has the 'lounge' & 'hall' cards or they are the solution
    # however, we know the solution is the kitchen
    # so we can infer that bob has both of these cards

    #     ROOMS:          bob  joe  meg
    #     hall___________ [ ]  [X]  [X]
    #     lounge_________ [ ]  [X]  [X]
    #     kitchen________ [X]  [X]  [X]

    # only possible if we know the section solution
    if section_solution is None:
        return

    # if the unknown cards are unique
    for card in section_cards:
        players_for_which_card_is_unknown = [
            player for player in game.players if player.is_unknown_card(card)
        ]
        if len(players_for_which_card_is_unknown) == 1:
            logging.debug(
                f"only {players_for_which_card_is_unknown[0].name} could have card {card}"
            )
            players_for_which_card_is_unknown[0].add_card(card)


def check_for_infer_sections(game):
    check_for_infer_section(game, game.WEAPONS, game.weapon_solution())
    check_for_infer_section(game, game.ROOMS, game.room_solution())
    check_for_infer_section(game, game.SUSPECTS, game.suspect_solution())


def check_for_infer_accusation(game):
    sol_weapon = game.weapon_solution()
    sol_suspect = game.suspect_solution()
    sol_room = game.room_solution()

    # todo early return
    for accusation in game.accusations:
        if accusation.suspect == sol_suspect and accusation.weapon == sol_weapon:
            # know accusation.room is not correct:
            game.add_not_solution(accusation.room)
        elif accusation.suspect == sol_suspect and accusation.room == sol_room:
            game.add_not_solution(accusation.weapon)
        elif accusation.room == sol_room and accusation.weapon == sol_weapon:
            game.add_not_solution(accusation.suspect)


def process_events(game, events):
    for event in events:
        if "q" in event:
            process_suggestion(game, event)
        elif "r" in event:
            process_reveal(game, event)
        elif "accuse" in event:
            game.add_failed_accusation(parse_suggestion(game, event["accuse"]))
        else:
            raise Exception("invalid event: " + event)

        while True:
            last_state = str(game)
            for player in game.players:
                # e.g. player responds to A B C but not X B C then player has A
                player.review_suggestions_for_inferrable_cards()
                # e.g. if player only has 1 card remaining & it could only be 1 card
                player.check_number_of_remaining_against_number_of_unknown()

            # sort of weird case where it's obvious where a card is when you already know the section solution,
            # and is only required to decrement the card count for a player
            check_for_infer_sections(game)

            # check for single missing answer
            check_for_completed_sections(game)

            # if accusation is A,B,C and confirmed B and C are solutions, then A is not the solution
            check_for_infer_accusation(game)

            cur_state = str(game)
            if last_state == cur_state:
                break


def init(game_setup):
    game = Game()
    if "cards" in game_setup:
        # overwrite cards
        game.SUSPECTS = set(game_setup["cards"]["suspects"])
        game.WEAPONS = set(game_setup["cards"]["weapons"])
        game.ROOMS = set(game_setup["cards"]["rooms"])

    cards = None
    player_with_cards = None
    for player_data in game_setup["players"]:
        player = Player(game, player_data["name"])
        if "cards" in player_data:
            player_with_cards = player
            # assume that player with supplied cards is user
            game.username = player_data["name"]
            cards = player_data["cards"].split()
        else:
            player.card_count = player_data["card_count"]
        game.add_player(player)

    player_with_cards.card_count = len(cards)
    for card in cards:
        player_with_cards.add_card(card)
    return game


def run(filename):
    with open(filename, "r") as file:
        # clear console
        os.system("cls" if os.name == "nt" else "clear")
        try:
            data = yaml.safe_load(file)
            game = init(data["setup"])
            process_events(game, data["events"])
            print(game)
        except Exception as e:
            print("waiting for valid game.yml")
            print(f"latest error: {e}")


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, filename) -> None:
        super().__init__()
        self.filename = filename

    def on_modified(self, event):
        logging.debug(f"modified: {event.src_path}")
        logging.debug(f"watching {self.filename}")
        if self.filename in os.path.basename(event.src_path):
            run(self.filename)


def start_watcher(filename):
    # Create an observer and event handler
    observer = Observer()
    event_handler = FileChangeHandler(filename)

    # Set the path to watch and start the observer
    path = "."
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "game.yml"
    run(filename)
    start_watcher(filename)
