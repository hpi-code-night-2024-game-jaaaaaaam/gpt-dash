from __future__ import annotations

import dataclasses
import random
import re
import time
import typing
import openaiAPI

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, send

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")


@dataclasses.dataclass
class Player:
    name: str
    session: Session
    score: int = 0
    answer: str = None
    votes: int = 0
    vote: int = None

    def send(self, message: str, role: str = "system"):
        self.session.send(message, role)


@dataclasses.dataclass
class Game:
    players: dict[str, Player] = dataclasses.field(default_factory=dict)
    vote_indexes: list[Player] | None = None
    prompt: str | None = None

    state: typing.Literal["answering", "voting", "results"] = "results"

    def add_player(self, id_: str, session: Session, name: str):
        self.players[id_] = Player(name, session)
        self.players[id_].send(f"You have joined the game as {name!r}.")

        if len(self.players) == 2:
            self.to_answering()

    def on_player_message(self, id_: str, message: str):
        player = self.players[id_]
        if self.state == "answering":
            player.answer = message
            player.send("Answer submitted.")
        elif self.state == "voting":
            try:
                vote_index = int(message)
                vote = self.vote_indexes[vote_index]
            except (ValueError, IndexError):
                player.send("Invalid vote. Please enter a number.")
                return
            else:
                player.vote = vote_index
                player.send(f"Vote submitted. ({vote_index})")
        elif self.state == "results":
            pass

    def to_voting(self):
        self.state = "voting"

        self.sendall("Generating LLM answer...")
        ai_answer = openaiAPI.answer_prompt(prompt=self.prompt)

        # noinspection PyTypeChecker
        self.vote_indexes = list(self.players.values()) + [Player(name="AI", session=None, answer=ai_answer)]
        random.shuffle(self.vote_indexes)

        for i, player in enumerate(self.vote_indexes):
            player.votes = 0

        for i, player in enumerate(self.players.values()):
            lines = ["Answers:"]
            for i, other_player in enumerate(self.vote_indexes):
                if other_player is player:
                    continue

                lines.append(f" ({i}) {other_player.answer}")

            player.send("\n".join(lines))

        self.sendall("Vote for the best answer!")

        self.countdown(120, lambda: all(player.vote is not None for player in self.players.values()))

        self.to_results()

    def to_results(self):
        self.state = "results"

        for player in self.players.values():
            vote = self.vote_indexes[player.vote]
            if vote.name == "AI":
                player.send("You voted for the AI. ✨ S L A Y ! ✨")
                player.score += 1
            else:
                vote.send(f"{player.name!r} voted for you. ✨ S L A Y ! ✨")
                vote.score += 1

        players_sorted_by_score = sorted(self.players.values(), key=lambda p: p.score, reverse=True)
        lines = ["Leaderboad:"]

        for i, player in enumerate(players_sorted_by_score):
            lines.append(f"{i + 1}. {player.name}: {player.score}")

        for player in self.players.values():
            player.send("\n".join(lines))

        time.sleep(10)

        self.to_answering()

    def to_answering(self):
        self.state = "answering"
        self.prompt = openaiAPI.get_random_prompt()

        for player in self.players.values():
            player.answer = None
            player.vote = None

        self.sendall(f"Prompt: {self.prompt}")

        self.countdown(120, lambda: all(player.answer is not None for player in self.players.values()))

        self.sendall("Time's up!")

        self.to_voting()

    def sendall(self, message: str, role: str = "system"):
        for player in self.players.values():
            player.send(message, role)

    def countdown(self, t: int, stopfunc: typing.Callable[[], bool]):
        # self.sendall(f"You have {t} seconds left to answer.")

        while (not stopfunc()) and (t > 0):
            print("ASD")
            mins, secs = divmod(t, 60)
            timer = '{:02d}:{:02d} left.'.format(mins, secs)
            self.sendall(timer)

            if t <= 10:
                time.sleep(1)
                t -= 1
            elif t <= 30:
                time.sleep(1)
                t -= 1
            else:
                for _ in range(30):
                    time.sleep(1)

                    if stopfunc():
                        return

                t -= 30


@dataclasses.dataclass
class Session:
    id_: str

    state: typing.Literal["lobby", "join-game", "login", "game"] = "lobby"

    current_game: Game | None = None

    def send(self, message: str, role: str = "system"):
        emit("response", {"data": message, "role": role}, to=self.id_)

    def init(self):
        self.send("Would you like to (1) create a new game, or (2) join an existing game?", "system")

    def lobby(self, option: str):
        if option == "1":
            new_game = Game()
            game_id = f"game{len(GAMES)}"
            GAMES[game_id] = new_game
            self.send(f"Created a game with game id: {game_id}")
            self.current_game = new_game
            self.send("Choose a unique username.")
            self.state = "login"
        elif option == "2":
            self.state = "join-game"
            self.send("Enter a valid game code.", "system")
        else:
            self.send("Input '1' or '2'.")

    def join_game(self, game_code: str):
        if game_code not in GAMES:
            self.send("Game does not exist.", "system")
        else:
            self.current_game = GAMES[game_code]
            self.send("Choose a unique username.")
            self.state = "login"

    def login(self, username: str):
        if username == "AI":
            self.send("Username is taken.", "system")
            return

        for player in self.current_game.players.values():
            if player.name == username:
                self.send("Username is taken.", "system")
                return

        self.send(f"Joining game as {username!r}!", "system")
        self.state = "game"
        self.current_game.add_player(self.id_, session=self, name=username)

    def game(self, message: str):
        self.current_game.on_player_message(self.id_, message)

    def on_message(self, message: str):
        self.send(message, "user")
        handler = self.state_message_handlers[self.state]
        handler(self, message)

    state_message_handlers: typing.ClassVar[dict] = {
        "lobby": lobby,
        "join-game": join_game,
        "login": login,
        "game": game,
    }


GAMES: dict[str, Game] = {}
SESSIONS: dict[str, Session] = {}


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('message')
def handle_message(data):
    print(f'Received message: {data} from {request.sid}')

    # emit('response', {'data': f'Server received: {data}'}, broadcast=True)

    SESSIONS[request.sid].on_message(data)


@socketio.on('connect')
def on_connect(data):
    emit("response", {"data": f"Your session id is {request.sid}"})

    emit("response", {"data": f"Willkommen! {request.sid}"}, to=request.sid)

    SESSIONS[request.sid] = Session(request.sid)
    SESSIONS[request.sid].init()


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
