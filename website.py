from threading import Thread

import flask
from scout_apm.flask import ScoutApm

app: flask.Flask = flask.Flask("")

# Attach ScoutApm to the Flask App
ScoutApm(app)

# Scout settings
app.config["SCOUT_NAME"] = "CYTsai's Discord Bot 1 Website"
# If you'd like to utilize Error Monitoring:
app.config["SCOUT_ERRORS_ENABLED"] = True


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
