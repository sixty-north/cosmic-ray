import unittest

from score_calculator import BowlingGame


class ScoreCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.game = BowlingGame()

    def test_create_bowling_game(self):
        self.assertIsInstance(self.game, BowlingGame)

    def test_the_score_of_a_new_game_is_zero(self):
        self.assertEqual(self.game.score(), 0)

    def test_the_count_of_a_roll_can_be_added_to_the_score(self):
        self.game.roll(2, 3)
        self.assertEqual(self.game.score(), 5)
