"""Tests for SD-01 demo.py — queue growth and capacity check.

Stdlib only, no pytest needed. Run:
    python -m unittest test_demo -v
"""
import unittest

from demo import queue_after_seconds, simulate, status


class TestQueue(unittest.TestCase):
    def test_queue_stays_zero_below_capacity(self):
        self.assertEqual(queue_after_seconds(arriving=50, capacity=100, seconds=5), 0)

    def test_queue_stays_zero_at_capacity(self):
        self.assertEqual(queue_after_seconds(arriving=100, capacity=100, seconds=5), 0)

    def test_queue_grows_above_capacity(self):
        # 250 - 100 = 150 extra per second, 5 seconds -> 750
        self.assertEqual(queue_after_seconds(arriving=250, capacity=100, seconds=5), 750)

    def test_queue_grows_second_by_second(self):
        self.assertEqual(
            simulate(arriving=250, capacity=100, seconds=3),
            [(1, 150), (2, 300), (3, 450)],
        )

    def test_scale_up_clears_queue(self):
        # Same load, bigger machine: no queue at all.
        self.assertEqual(queue_after_seconds(arriving=250, capacity=380, seconds=5), 0)

    def test_status(self):
        self.assertEqual(status(250, 100), "line lagegi")
        self.assertEqual(status(250, 380), "sambhal gaya")
        self.assertEqual(status(100, 100), "sambhal gaya")


if __name__ == "__main__":
    unittest.main(verbosity=2)
