import dataclasses


@dataclasses.dataclass
class Player:
    name: str
    score: int = 0


@dataclasses.dataclass
class Game:
    players: dict[str, Player]

    def add_player(self, name: str):
        ...

    def submit_answer(self, player_id: str, answer: str):
        ...
