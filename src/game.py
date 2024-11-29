import dataclasses
import typing


@dataclasses.dataclass
class Player:
    name: str
    score: int = 0

    def send(self, message: str):
        ...


@dataclasses.dataclass
class Game:
    players: dict[str, Player]
