import unittest
from game_logic.game_model import Minefield, CellState, GameState, random_minefield

class TestMinefield(unittest.TestCase):
    def test_init_has_no_selected_cell_state(self):
        mf = Minefield(5, 5, {"0,0"})
        self.assertFalse(hasattr(mf, 'x'))
        self.assertFalse(hasattr(mf, 'y'))
        self.assertEqual(mf.width, 5)
        self.assertEqual(mf.height, 5)

    def test_to_dict_and_from_dict(self):
        mf = Minefield(4, 4, {"1,1"})
        mf.reveal_cell(0, 0)
        d = mf.to_dict()
        self.assertNotIn("x", d)
        self.assertNotIn("y", d)

        mf2 = Minefield.from_dict(d)
        self.assertFalse(hasattr(mf2, 'x'))
        self.assertFalse(hasattr(mf2, 'y'))
        self.assertEqual(mf2.width, 4)
        self.assertEqual(mf2.height, 4)
        self.assertEqual(mf2.state, GameState.IN_PROGRESS)

    def test_flag_and_reveal_cell(self):
        mf = Minefield(3, 3, {"2,2"})
        mf.flag_cell(0, 0)
        self.assertEqual(mf.get_cell(0, 0).state, CellState.FLAGGED)
        mf.flag_cell(0, 0)
        self.assertEqual(mf.get_cell(0, 0).state, CellState.UNKNOWN)
        mf.reveal_cell(0, 0)
        self.assertNotEqual(mf.get_cell(0, 0).state, CellState.UNKNOWN)

if __name__ == "__main__":
    unittest.main()
