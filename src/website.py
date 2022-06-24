import os
from threading import Thread

import flask

app: flask.Flask = flask.Flask("")


@app.route("/img/<img>")
def image(img):
    img_base_path = f"{os.getcwd()}/web_assets/img/"
    return flask.send_from_directory(img_base_path, img)


@app.route("/")
def home():
    return flask.render_template("index.html")


def run():
    app.run(host="0.0.0.0", port=8080)


def alive():
    t = Thread(target=run)
    t.start()


if __name__ == "__main__":
    alive()
