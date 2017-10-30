import unittest

from score_calculator import BowlingGame


class ScoreCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.game = BowlingGame()

    def test_create_bowling_game(self):
        self.assertIsInstance(self.game, BowlingGame)

    def test_the_score_of_a_new_game_is_zero(self):
        self.assertEqual(self.game.score(), 0)

    def test_the_count_of_the_first_frame_is_added_to_the_score(self):
        self.game.roll(2, 3)
        self.assertEqual(self.game.score(), 5)

    def test_multiple_frame_results_are_kept_in_the_score(self):
        self.game.roll(2, 4)
        self.game.roll(6, 2)
        self.assertEqual(self.game.score(), 14)

    def test_spares_are_detected_for_the_next_frame(self):
        self.game.roll(6, 4)
        self.assertTrue(self.game.spare)

    def test_previous_spare_results_in_that_next_roll_points_are_doubled(self):
        self.game.roll(6, 4)
        self.game.roll(5, 3)
        self.assertEqual(self.game.score(), 23)

    def test_double_spares_are_counted_correctly(self):
        self.game.roll(6, 4)
        self.game.roll(5, 5)
        self.game.roll(8, 0)
        self.assertEqual(self.game.score(), 41)

    def test_the_spare_flag_is_removed_in_the_next_frame(self):
        self.game.roll(6, 4)
        self.game.roll(1, 1)
        self.game.roll(2, 0)
        self.assertEqual(self.game.score(), 15)

    def test_a_strike_is_detected_and_no_spare_flag_is_set(self):
        self.game.roll(10, 0)
        self.assertTrue(self.game.strike)
        self.assertFalse(self.game.spare)

    def test_previous_strike_doubles_the_next_frame_pin_count(self):
        self.game.roll(10, 0)
        self.game.roll(5, 4)
        self.assertEqual(self.game.score(), 28)

    def test_the_strike_flag_is_removed_in_the_next_frame(self):
        self.game.roll(10, 0)
        self.game.roll(1, 1)
        self.game.roll(2, 5)
        self.assertEqual(self.game.score(), 21)

        # case with strike after spare or the way around
