from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import numpy as np
import time
import ast
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
        rdv_values = db_connector.fetch_matrix_values(configParameters["numDopplerBins"],
                                                      configParameters["numRangeBins"])
        meta_data = db_connector.fetch_data("Prediction", "Score", "Detected objects", "Time")[-1]

        prediction_value = True if meta_data[1] == "human_present" else False
        score = meta_data[3]
        detected_object_distances = list(ast.literal_eval(meta_data[5].strip().strip('[]')))
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
