from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/login/<discord_id>")
def login(discord_id):
    return f"Login with Discord ID: {discord_id}"
