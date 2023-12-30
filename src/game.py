COL_1_WIDTH = 15


class Game:
    def __init__(self):
        self.SUSPECTS = {"green", "mustard", "peacock", "plum", "scarlet", "white"}
        self.ROOMS = {
            "study",
            "hall",
            "lounge",
            "library",
            "billiard",
            "dining",
            "conservatory",
            "ballroom",
            "kitchen",
        }
        self.WEAPONS = {
            "candlestick",
            "dagger",
            "leadpipe",
            "revolver",
            "rope",
            "wrench",
        }
        self._suspect_solution = None
        self._room_solution = None
        self._weapon_solution = None
        self.players = []
        self.accusations = []
        self.not_solution_cards = []
        self.username = None

    def all_cards(self):
        return self.SUSPECTS | self.ROOMS | self.WEAPONS

    def add_player(self, player):
        self.players.append(player)

    def add_failed_accusation(self, accuse):
        self.accusations.append(accuse)

    # append cards that are not the solution but the owner is not known
    def add_not_solution(self, card):
        self.not_solution_cards.append(card)

    def get_section_solution(self, section_cards):
        for section_card in section_cards:
            does_not_have_count = 0
            for player in self.players:
                if section_card in player.all_known_does_not_have_cards():
                    does_not_have_count += 1
            if does_not_have_count == len(self.players):
                return section_card
        return None

    def suspect_solution(self):
        if self._suspect_solution is None:
            self._suspect_solution = self.get_section_solution(self.SUSPECTS)
        return self._suspect_solution

    def weapon_solution(self):
        if self._weapon_solution is None:
            self._weapon_solution = self.get_section_solution(self.WEAPONS)
        return self._weapon_solution

    def room_solution(self):
        if self._room_solution is None:
            self._room_solution = self.get_section_solution(self.ROOMS)
        return self._room_solution

    def is_solved(self):
        return (
            self.suspect_solution() is not None
            and self.weapon_solution() is not None
            and self.room_solution() is not None
        )

    def get_player(self, name):
        for player in self.players:
            if player.name == name:
                return player
        raise Exception("invalid player name: " + name)

    def _section_str(self, section_cards):
        # Print card grid
        ret = ""
        for section_card in sorted(list(section_cards)):
            does_not_have_count = 0
            row = f"{section_card:_<{COL_1_WIDTH}}"  # Left-align
            for player in self.players:
                # player has this card
                if section_card in player.all_known_cards():
                    row += " [!] "
                # player does not have one of these cards
                elif section_card in player.all_known_does_not_have_cards():
                    does_not_have_count += 1
                    row += " [X] "
                # player has one of the cards with these symbols
                elif section_card in player.all_suggestions_with_no_answer_cards():
                    row += " [⁈] "
                # player might have this card but this card is not the solution
                elif section_card in self.not_solution_cards:
                    row += " [-] "
                else:
                    row += " [ ] "
            if does_not_have_count == len(self.players):
                row = row.replace(f"[X]", f"[A]")
            ret += row + "\n"

        return ret

    def __str__(self):
        player_header = " "
        for player in self.players:
            player_header += f" {player.name[:3]} "

        ret = ""
        ret += f"{'\nSUSPECTS:': <{COL_1_WIDTH}}{player_header}\n"
        ret += self._section_str(self.SUSPECTS)
        ret += f"{'\nWEAPONS:': <{COL_1_WIDTH}}{player_header}\n"
        ret += self._section_str(self.WEAPONS)
        ret += f"{'\nROOMS:': <{COL_1_WIDTH}}{player_header}\n"
        ret += self._section_str(self.ROOMS)
        if self.is_solved():
            ret += f"***SOLVED: {self._suspect_solution} in the {self._room_solution} with the {self._weapon_solution}***"
        return ret
