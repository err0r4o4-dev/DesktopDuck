from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from desktop_duck.behavior import DuckBehavior
from desktop_duck.config import AppConfig, ConfigStore


class ConfigTests(unittest.TestCase):
    def test_invalid_values_are_normalized(self) -> None:
        config = AppConfig.from_mapping(
            {"size": 99, "speed": "not-a-number", "messages": []}
        )
        self.assertEqual(config.size, 2.0)
        self.assertEqual(config.speed, 3.0)
        self.assertTrue(config.messages)

    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ConfigStore(Path(directory) / "config.json")
            expected = AppConfig(size=1.4, messages=["quack"])
            store.save(expected)
            self.assertEqual(store.load(), expected)


class BehaviorTests(unittest.TestCase):
    def test_duck_bounces_at_left_edge(self) -> None:
        config = AppConfig(avoid_mouse=False)
        behavior = DuckBehavior(0, config)
        behavior.velocity = -100
        behavior.target_velocity = -100
        snapshot = behavior.update(
            0.033, 0, 1920, 240, (5000, 5000), 900, config
        )
        self.assertEqual(snapshot.x, 0)
        self.assertEqual(snapshot.direction, 1)
        self.assertTrue(snapshot.bumped)

    def test_manual_sleep_state_is_kept(self) -> None:
        config = AppConfig(avoid_mouse=False)
        behavior = DuckBehavior(100, config)
        behavior.trigger("sleep", 5)
        snapshot = behavior.update(
            0.033, 0, 1920, 240, (5000, 5000), 900, config
        )
        self.assertEqual(snapshot.state, "sleep")


if __name__ == "__main__":
    unittest.main()
