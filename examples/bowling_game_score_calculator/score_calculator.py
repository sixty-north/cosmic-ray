"""
This is a simple class to demonstrate the cosmic-ray library.
The BowlingGame class keeps and calculates the score of a ten-pin bowling
game for one player.
"""

class BowlingGame():
    def __init__(self):
        self.score_count = 0

    def score(self):
        return self.score_count

    def roll(self, first_roll, second_roll):
        roll_result = first_roll + second_roll
        self.score_count += roll_result
