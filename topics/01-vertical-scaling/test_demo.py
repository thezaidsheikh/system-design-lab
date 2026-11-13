"""SD-01 · Vertical scaling — queue-growth aur capacity-check ke tests.

Sirf standard library (unittest). Chalana:

    python -m unittest discover -s topics/01-vertical-scaling -v
    # ya repo root se:
    python -m unittest discover -s topics/01-vertical-scaling
"""

import unittest

from demo import is_overloaded, queue_after_seconds, simulate


class TestQueueGrowth(unittest.TestCase):
    def test_load_below_capacity_queue_stays_zero(self):
        # 50 RPS load, 100 RPS capacity — har second sab serve ho jata hai.
        self.assertEqual(queue_after_seconds(100, 50, 5), 0)

    def test_load_equal_to_capacity_queue_stays_zero(self):
        # Kinare par, par abhi tak line nahi lagi.
        self.assertEqual(queue_after_seconds(100, 100, 5), 0)

    def test_load_above_capacity_queue_grows_every_second(self):
        # 250 load - 100 capacity = har second 150 line me judte hain.
        self.assertEqual(queue_after_seconds(100, 250, 5), 750)
        self.assertEqual(queue_after_seconds(100, 250, 1), 150)
        self.assertEqual(queue_after_seconds(100, 250, 2), 300)

    def test_queue_drains_when_load_drops_below_capacity(self):
        # 2 second overload se queue 300 ki ho gayi; phir load 0 ho gaya to
        # queue 100/sec drain hoti hai — 3 second me khaali, aur neeche nahi.
        queued = queue_after_seconds(100, 250, 2)
        self.assertEqual(queued, 300)
        self.assertEqual(queue_after_seconds(100, 0, 3, initial_queue=queued), 0)
        # 1 second me sirf 100 drain hoti hai — 200 abhi bhi khadi hai.
        self.assertEqual(queue_after_seconds(100, 0, 1, initial_queue=queued), 200)

    def test_zero_seconds_means_empty_queue(self):
        self.assertEqual(queue_after_seconds(100, 250, 0), 0)

    def test_invalid_capacity_raises(self):
        with self.assertRaises(ValueError):
            queue_after_seconds(0, 250, 5)
        with self.assertRaises(ValueError):
            queue_after_seconds(-10, 250, 5)

    def test_negative_seconds_raises(self):
        with self.assertRaises(ValueError):
            queue_after_seconds(100, 250, -1)


class TestCapacityCheck(unittest.TestCase):
    def test_below_and_equal_are_not_overloaded(self):
        self.assertFalse(is_overloaded(100, 50))
        self.assertFalse(is_overloaded(100, 100))

    def test_above_is_overloaded(self):
        self.assertTrue(is_overloaded(100, 101))
        self.assertTrue(is_overloaded(100, 250))

    def test_scaled_up_machine_handles_the_same_load(self):
        # Wahi 250 RPS jo chhoti machine (100) par overload tha,
        # badi machine (380) par aaram se sambhal jata hai.
        self.assertTrue(is_overloaded(100, 250))
        self.assertFalse(is_overloaded(380, 250))
        self.assertEqual(queue_after_seconds(380, 250, 5), 0)


class TestSimulationRows(unittest.TestCase):
    def test_each_second_has_one_row(self):
        self.assertEqual(len(simulate(100, 250, 5)), 5)

    def test_queue_grows_second_by_second_in_rows(self):
        queues = [row.queue for row in simulate(100, 250, 5)]
        self.assertEqual(queues, [150, 300, 450, 600, 750])

    def test_wait_time_grows_with_queue(self):
        rows = simulate(100, 250, 5)
        waits = [row.wait_seconds for row in rows]
        self.assertEqual(waits, [1.5, 3.0, 4.5, 6.0, 7.5])
        # Queue badhti hai to intezaar bhi badhta hai — latency "phat" rahi hai.
        self.assertTrue(all(a < b for a, b in zip(waits, waits[1:])))

    def test_below_capacity_serves_everything_with_no_wait(self):
        rows = simulate(100, 50, 5)
        self.assertTrue(all(row.queue == 0 for row in rows))
        self.assertTrue(all(row.wait_seconds == 0 for row in rows))
        self.assertTrue(all(row.served == 50 for row in rows))

    def test_at_capacity_serves_everything_but_no_headroom(self):
        rows = simulate(100, 100, 5)
        self.assertTrue(all(row.queue == 0 for row in rows))
        self.assertTrue(all(row.served == 100 for row in rows))


if __name__ == "__main__":
    unittest.main()
