from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import numpy as np
import time
import os
import threading
from database_class import DatabaseConnector
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

script_dir = os.path.dirname(os.path.abspath(__file__))

db_connector = DatabaseConnector(f"{script_dir}/radar_database.db")
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
        rdv_values = db_connector.fetch_matrix_values(configParameters["numDopplerBins"], configParameters["numRangeBins"])
        meta_data = db_connector.fetch_data("Prediction", "Score", "Detected objects", "Time")[-1]

        if meta_data[1] == "Human_Present":
            prediction_value = True
        else:
            prediction_value = False

        score = meta_data[3]

        detected_object_distances = [float(value) for value in meta_data[5].strip("[]").split()]

        time_stamp = meta_data[7]

        socketio.emit('data', {'x': rangeArray.tolist(), 'y': dopplerArray.tolist(), 'z': rdv_values.tolist(),
                               'classification': prediction_value,
                               'detected_object_distances': detected_object_distances,
                               'time_stamp': time_stamp}, namespace='/')
        time.sleep(0.1)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    t = threading.Thread(target=emit_data)
    t.daemon = True
    t.start()
    socketio.run(app, host="0.0.0.0", allow_unsafe_werkzeug=True)
