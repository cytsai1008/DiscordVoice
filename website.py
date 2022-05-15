from threading import Thread

import flask

app: flask.Flask = flask.Flask("")


@app.route("/")
def home():
    return "hello, UpTimeRobot!"


def run():
    app.run(host="0.0.0.0", port=8080)


def alive():
    t = Thread(target=run)
    t.start()


if __name__ == "__main__":
    alive()
