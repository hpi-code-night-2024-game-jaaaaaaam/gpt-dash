import dataclasses
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

    state: typing.Literal["lobby", "game"] = "lobby"
    game: Game | None = None

    def send(self, message: str, role: str):
        emit("response", {"data": f"{role}: {message}"}, to=self.id_)

    def init(self):
        ...

    def on_message(self, message: str):
        if self.state == "lobby":
            ...

        print(f"SESSION ON MESSAGE, {message}")
        self.send("You said: " + message, "server")


GAMES: dict[str, Game] = {}
SESSIONS: dict[str, Session] = {}


@app.route('/')
def index():
    return render_template('web/index.html')


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

+
if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
