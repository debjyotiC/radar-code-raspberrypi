from flask import Flask, render_template
import numpy as np
import sqlite3
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

configParameters = {'numDopplerBins': 16, 'numRangeBins': 128, 'rangeResolutionMeters': 0.04360212053571429,
                    'rangeIdxToMeters': 0.04360212053571429, 'dopplerResolutionMps': 0.12518841691334906,
                    'maxRange': 10.045928571428572, 'maxVelocity': 2.003014670613585}  # AWR2944X_Deb


@app.route('/')
def occupancy_results():
    conn = sqlite3.connect(f'{script_dir}/radar_database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM radar_data WHERE key_1=? AND key_2=?", ("Prediction", "Time"))
    result = c.fetchall()[-1]

    results = {
        'Prediction': result[1],
        'Time': result[3]
    }

    c.execute("SELECT matrix_values FROM rdv_mat ORDER BY id DESC LIMIT 1")
    result_2 = c.fetchall()[-1]
    values_blob_2 = result_2[0]

    # Convert the binary data back to a 2D NumPy array
    rdv_matrix = np.frombuffer(values_blob_2, dtype=np.float32).reshape((16, 128))

    rangeArray = np.array(range(configParameters["numRangeBins"])) * configParameters["rangeIdxToMeters"]
    dopplerArray = np.multiply(
        np.arange(-configParameters["numDopplerBins"] / 2, configParameters["numDopplerBins"] / 2),
        configParameters["dopplerResolutionMps"])

    return render_template('index.html', results=results, x=rangeArray, y=dopplerArray, z=rdv_matrix)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050)
