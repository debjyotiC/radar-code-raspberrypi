from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import numpy as np
import time
import threading
from database_class import DatabaseConnector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
socketio = SocketIO(app)

db_connector = DatabaseConnector("radar_database.db")
db_connector.connect()

configParameters = {'numDopplerBins': 16, 'numRangeBins': 256, 'rangeResolutionMeters': 0.146484375,
                    'rangeIdxToMeters': 0.146484375, 'dopplerResolutionMps': 0.1252347734553042, 'maxRange': 33.75,
                    'maxVelocity': 1.0018781876424336}

rangeArray = np.array(range(configParameters["numRangeBins"])) * configParameters["rangeIdxToMeters"]
dopplerArray = np.multiply(
    np.arange(-configParameters["numDopplerBins"] / 2, configParameters["numDopplerBins"] / 2),
    configParameters["dopplerResolutionMps"])


def emit_data():
    while True:
        classification_time_stamp = db_connector.fetch_data("Prediction", "Time")[-1]
        rdv_values = db_connector.fetch_matrix_values(configParameters["numDopplerBins"],
                                                      configParameters["numRangeBins"])
        socketio.emit('data', {'x': rangeArray.tolist(), 'y': dopplerArray.tolist(), 'z': rdv_values.tolist(),
                               'classification': classification_time_stamp[1]}, namespace='/')
        time.sleep(0.5)


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect', namespace='/')
def connect():
    classification_time_stamp = db_connector.fetch_data("Prediction", "Time")[-1]
    rdv_values = db_connector.fetch_matrix_values(configParameters["numDopplerBins"], configParameters["numRangeBins"])
    emit('data', {'x': rangeArray.tolist(), 'y': dopplerArray.tolist(), 'z': rdv_values.tolist(),
                  'classification': classification_time_stamp[1]})


@socketio.on('data', namespace='/')
def update_data():
    classification_time_stamp = db_connector.fetch_data("Prediction", "Time")[-1]
    rdv_values = db_connector.fetch_matrix_values(configParameters["numDopplerBins"], configParameters["numRangeBins"])
    emit('data',
         {'x': rangeArray.tolist(), 'y': dopplerArray.tolist(), 'z': rdv_values.tolist(),
          'classification': classification_time_stamp[1]})


if __name__ == '__main__':
    t = threading.Thread(target=emit_data)
    t.daemon = True
    t.start()
    socketio.run(app, host="0.0.0.0", allow_unsafe_werkzeug=True)
