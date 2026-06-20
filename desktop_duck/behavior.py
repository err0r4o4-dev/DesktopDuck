from __future__ import annotations

import math
import random
from dataclasses import dataclass

from desktop_duck.config import AppConfig


@dataclass(frozen=True, slots=True)
class BehaviorSnapshot:
    x: float
    state: str
    direction: int
    should_talk: bool = False
    bumped: bool = False


class DuckBehavior:
    """Small state machine responsible for believable desktop wandering."""

    def __init__(self, x: float, config: AppConfig) -> None:
        self.x = x
        self.velocity = config.speed * 28.0
        self.target_velocity = self.velocity
        self.direction = 1
        self.state = "walk"
        self.state_remaining = random.uniform(2.5, 6.0)
        self.decision_remaining = random.uniform(2.5, 7.0)
        self.talk_remaining = random.uniform(
            config.talk_min_seconds, config.talk_max_seconds
        )
        self.avoid_remaining = 0.0

    def place(self, x: float) -> None:
        self.x = x

    def trigger(self, state: str, duration: float) -> None:
        if state not in {"walk", "idle", "sleep", "happy"}:
            return
        self.state = state
        self.state_remaining = duration
        if state != "walk":
            self.target_velocity = 0.0

    def update(
        self,
        seconds: float,
        left: float,
        right: float,
        width: float,
        pointer: tuple[float, float],
        center_y: float,
        config: AppConfig,
    ) -> BehaviorSnapshot:
        seconds = max(0.0, min(seconds, 0.08))
        bumped = False
        should_talk = False
        base_speed = config.speed * 28.0

        self.state_remaining -= seconds
        self.decision_remaining -= seconds
        self.talk_remaining -= seconds
        self.avoid_remaining = max(0.0, self.avoid_remaining - seconds)

        center_x = self.x + width / 2
        pointer_distance = math.hypot(pointer[0] - center_x, pointer[1] - center_y)
        if config.avoid_mouse and pointer_distance < 155:
            self.state = "walk"
            self.state_remaining = 1.0
            self.avoid_remaining = 0.9
            away = -1 if pointer[0] > center_x else 1
            self.target_velocity = away * base_speed * 1.85
        elif self.avoid_remaining <= 0:
            self._update_state(base_speed)

        acceleration = max(180.0, base_speed * 4.0)
        difference = self.target_velocity - self.velocity
        maximum_change = acceleration * seconds
        self.velocity += max(-maximum_change, min(maximum_change, difference))

        if self.state in {"idle", "sleep", "happy"}:
            self.target_velocity = 0.0

        self.x += self.velocity * seconds
        maximum_x = max(left, right - width)
        if self.x <= left:
            self.x = left
            self.direction = 1
            self.target_velocity = abs(base_speed)
            bumped = True
        elif self.x >= maximum_x:
            self.x = maximum_x
            self.direction = -1
            self.target_velocity = -abs(base_speed)
            bumped = True
        elif abs(self.velocity) > 2:
            self.direction = 1 if self.velocity > 0 else -1

        if self.talk_remaining <= 0:
            should_talk = True
            self.talk_remaining = random.uniform(
                config.talk_min_seconds, config.talk_max_seconds
            )

        return BehaviorSnapshot(
            x=self.x,
            state=self.state,
            direction=self.direction,
            should_talk=should_talk,
            bumped=bumped,
        )

    def _update_state(self, base_speed: float) -> None:
        if self.state_remaining <= 0 and self.state != "walk":
            self.state = "walk"
            self.state_remaining = random.uniform(3.0, 7.0)
            self.target_velocity = self.direction * base_speed

        if self.decision_remaining > 0 or self.state != "walk":
            return

        choice = random.random()
        if choice < 0.55:
            self.state = "idle"
            self.state_remaining = random.uniform(1.5, 3.5)
            self.target_velocity = 0.0
        elif choice < 0.68:
            self.state = "sleep"
            self.state_remaining = random.uniform(5.0, 10.0)
            self.target_velocity = 0.0
        else:
            self.direction *= -1
            self.target_velocity = self.direction * base_speed * random.uniform(0.8, 1.2)
        self.decision_remaining = random.uniform(3.0, 8.0)
