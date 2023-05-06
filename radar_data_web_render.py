from flask import Flask, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)


@app.route("/")
def index():
    conn = sqlite3.connect('radar_database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM radar_data WHERE key_1=? AND key_2=?", ("Prediction", "Time"))
    result = c.fetchall()[-1]

    reply = {'Prediction': result[1], 'Time': result[3]}

    return render_template("index.html", results=reply)


if __name__ == '__main__':
    app.run(host='192.168.0.111', port=5050)
