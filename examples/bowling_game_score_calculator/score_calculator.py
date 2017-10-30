"""
This is a simple class to demonstrate the cosmic-ray library.
The BowlingGame class keeps and calculates the score of a ten-pin bowling
game for one player.
The traditional bowling scoring is used:
https://en.wikipedia.org/wiki/Ten-pin_bowling#Traditional_scoring
"""


ALL_PINS = 10

class BowlingGame():
    def __init__(self):
        self.score_count = 0
        self.spare = False
        self.strike = False

    def score(self):
        return self.score_count

    def roll(self, first_roll, second_roll):
        frame_result = first_roll + second_roll
        self._handle_spare_and_strikes(first_roll, frame_result)
        self.score_count += frame_result

    def _handle_spare_and_strikes(self, first_roll, frame_result):
        self._award_previous_spare_count(first_roll)
        self._award_previous_strike_count(frame_result)
        self._check_for_strike(first_roll)
        self._check_for_spare(frame_result)

    def _award_previous_spare_count(self, first_roll):
        if self.spare == True:
            self.score_count += first_roll
            self.spare = False

    def _award_previous_strike_count(self, frame_result):
        if self.strike == True:
            self.score_count += frame_result
            self.strike = False

    def _check_for_strike(self, first_roll):
        if first_roll == ALL_PINS:
            self.strike = True

    def _check_for_spare(self, frame_result):
        if frame_result == ALL_PINS and not self.strike:
            self.spare = True
