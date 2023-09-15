# run: python3 main.py

# Import necessary modules
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

# Initialize the Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "jacamcacaoicnalc"
socketio = SocketIO(app)

# Create a dictionary to store chat rooms and their information
rooms = {}


# Function to generate a unique code for chat rooms
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code


# Define the root route for the home page
@app.route("/", methods=["POST", "GET"])
def home():
    # Clear session data when on the home page
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        # Check if the user entered a name
        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        # Check if the user entered a room code when trying to join
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)

        room = code
        if create != False:
            # Generate a unique room code if the user is creating a room
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)

        # Store user data in a session stored on the server
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

# Define the route for the chat room page


@app.route("/room")
def room():
    # Check if the user filled out the form correctly to access the chat room
    room = session.get("room")
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

# Define the event handler for sending messages via SocketIO


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

# Define the event handler for connecting to the chat room via SocketIO


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    # Check if the user has a room or name
    if not room or not name:
        return

    # Leave the room if the user is not in the correct room
    if room not in rooms:
        leave_room(room)
        return

    # Room exists, join the room
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

# Define the event handler for disconnecting from the chat room via SocketIO


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        # If all users have left the room, delete the room
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left room {room}")


# Run the Flask application with SocketIO
if __name__ == "__main__":
    socketio.run(app, debug=True)  # Automatically refresh
