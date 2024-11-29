import dataclasses
import re
import typing

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, send

from src.game import Game

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)


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
            self
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
            self.state = "game"
            self.send("Joining game!", "system")
            self.current_game.add_player()

    def login(self, username: str):
        ...

    def game(self, message: str):
        self.game.on_player_message(message)

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
