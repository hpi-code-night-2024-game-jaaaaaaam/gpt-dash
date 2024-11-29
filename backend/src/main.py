from __future__ import annotations

import dataclasses
import random
import re
import typing

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, send
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
# app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)


@dataclasses.dataclass
class Player:
    name: str
    session: Session
    score: int = 0
    answer = ""
    votes: int = 0

    def send(self, message: str, role: str = "system"):
        self.session.send(message, role)


@dataclasses.dataclass
class Game:
    players: dict[str, Player] = dataclasses.field(default_factory=dict)
    vote_indexes: list[Player] | None = None

    state: typing.Literal["answering", "voting", "results"] = "results"

    def add_player(self, id_: str, session: Session, name: str):
        self.players[id_] = Player(name, session)
        self.players[id_].send(f"You have joined the game as {name!r}.")

    def on_player_message(self, id_: str, message: str):
        player = self.players[id_]
        if self.state == "answering":
            player.answer = message
            player.send("Answer submitted.")
        elif self.state == "voting":
            try:
                vote_index = int(message)
                player = self.vote_indexes[vote_index]
            except (ValueError, IndexError):
                player.send("Invalid vote. Please enter a number.")
                return
            else:
                vote = self.vote_indexes[vote_index]
                vote.votes += 1
                player.send("Vote submitted.")

    def to_voting(self):
        self.vote_indexes = list(self.players.values())
        random.shuffle(self.vote_indexes)

        lines = ["Answers:"]

        for i, player in enumerate(self.vote_indexes):
            player.votes = 0
            lines.append(f" ({i}) {player.answer}")

        for player in self.players.values():
            player.send("\n".join(lines))
            player.send("Vote for the best answer!")

    def to_results(self):
        ...

    def to_answering(self):
        ...

@dataclasses.dataclass
class Session:
    id_: str

    state: typing.Literal["lobby", "join-game", "login", "game"] = "lobby"

    current_game: Game | None = None

    def send(self, message: str, role: str = "system"):
        emit("response", {"data": f"{role}: {message}"}, to=self.id_)

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
        for player in self.current_game.players.values():
            if player.name == username:
                self.send("Username is taken.", "system")
                return

        self.send(f"Joining game as {username!r}!", "system")
        self.state = "game"
        self.current_game.add_player(self.id_, session=self, name="Player")

    def game(self, message: str):
        self.current_game.on_player_message(self.id_, message)

    def on_message(self, message: str):
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

    emit('response', {'data': f'Server received: {data}'}, broadcast=True)

    SESSIONS[request.sid].on_message(data)


@socketio.on('connect')
def on_connect(data):
    emit("response", {"data": f"Your session id is {request.sid}"})

    emit("response", {"data": f"Willkommen! {request.sid}"}, to=request.sid)

    SESSIONS[request.sid] = Session(request.sid)
    SESSIONS[request.sid].init()


if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
