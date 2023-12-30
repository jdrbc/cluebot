class Suggestion:
    def __init__(self, player_name, suspect=None, weapon=None, room=None):
        self.player_name = player_name
        self.suspect = suspect
        self.weapon = weapon
        self.room = room
        self.solved = False

    def __str__(self):
        return f"{self.player_name} guesses: {self.suspect}, {self.weapon}, {self.room}"
