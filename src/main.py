from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, send

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('web/index.html')


@socketio.on('message')
def handle_message(message):
    print(f'Received message: {message}')
    emit('response', {'data': f'Server received: {message}'}, broadcast=True)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', to=room)



if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
