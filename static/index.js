window.onload = function () {
  var iconWithMsg = document.getElementById("iconWithMsg");
  var alarmSound = document.getElementById("alarmSound");
  var objectLists = document.getElementById("objectLists");
  var noOfObjects = document.getElementById("noOfObjects");
  var showNoSound = document.getElementById("showNoSound");
  
  showNoSound.innerHTML = `<img
          src="static/silent-line-icon.png"
          style="height: 15px; width: 15px; margin-bottom: 3px"
        />`;
  showNoSound.addEventListener("click", function () {
    showNoSound.innerHTML = `<img
          src="static/volume-line-icon.png"
          style="height: 15px; width: 15px; margin-bottom: 3px"
        />`;
  });

  document.addEventListener("click", () => {
    showNoSound.innerHTML = `<img
    src="static/volume-line-icon.png"
    style="height: 15px; width: 15px; margin-bottom: 3px"
  />`;
  });

  // Additional actions...
  var socket = io.connect("http://" + document.domain + ":" + location.port);

  socket.on("data", function (data) {
    var x = data.x;
    var y = data.y;
    var z = data.z;
    var classification = data.classification;

    var layout = {
      title: {
        text: "Range-Doppler Plot",
      },
      autosize: true,
      margin: { t: 50, r: 20, b: 20, l: 50, pad: 1 },
      xaxis: {
        automargin: true,
        title: {
          text: "Range (m)",
          standoff: 25,
        },
        titlefont: {
          size: 16,
          color: "#333",
        },
      },
      yaxis: {
        automargin: true,
        title: {
          text: "Doppler velocity (m/s^2)",
          standoff: 10,
        },
        titlefont: {
          size: 16,
          color: "#333",
        },
      },
    };
    let noOfObject = data.detected_object_distances.length;
    noOfObjects.innerText = `No of Object detected : ${noOfObject}`;

    let objectListsHtml = ``;
    for (let i = 0; i < noOfObject; i++) {
      objectListsHtml += `<div class="message">
                    <div class="message-content">Obj: ${i + 1}, Distance: ${
        data.detected_object_distances[i]
      } ft.</div>
                  </div>`;
    }
    objectLists.innerHTML = objectListsHtml;

    if (classification) {
      Plotly.react(
        "plotly-container",
        [
          {
            x: x,
            y: y,
            z: z,
            type: "contour",
            colorscale: [
              ["0.0", "#440000 "],
              ["0.301029995663981", "#550000"],
              ["0.477121254719662", "#660000"],
              ["0.602059991327962", "#880000"],
              ["0.698970004336018", "#A00000"],
              ["0.778151250383643", "#BB0000"],
              ["0.845098040014256", "#CF0000"],
              ["0.903089986991943", "#EF0000"],
              ["0.954242509439324", "#FF0000"],
              ["1.0", "#FFF000"],
            ],
            contours: {
              showlines: false,
              smooth: true,
            },
            showscale: false,
          },
        ],
        layout
      );
      iconWithMsg.innerHTML = `<img
          class="ripple-effect"
          src="static/red-circle.png"
          style="height: 15px; width: 15px; margin-bottom: 3px"
        /> Occupied - Human presence detected`;
      alarmSound.play();
    } else {
      Plotly.react(
        "plotly-container",
        [
          {
            x: x,
            y: y,
            z: z,
            type: "contour",
            colorscale: [
              ["0.0", "#004400 "],
              ["0.301029995663981", "#005500"],
              ["0.477121254719662", "#006600"],
              ["0.602059991327962", "#008800"],
              ["0.698970004336018", "#00A000"],
              ["0.778151250383643", "#00BB00"],
              ["0.845098040014256", "#00CF00"],
              ["0.903089986991943", "#00EF00"],
              ["0.954242509439324", "#00FF00"],
              ["1.0", "#00FF00"],
            ],
            contours: {
              showlines: false,
              smooth: true,
            },
            showscale: false,
          },
        ],
        layout
      );

      iconWithMsg.innerHTML = `<img
          class="ripple-effect"
          src="static/green-circle-icon.png"
          style="height: 15px; width: 15px; margin-bottom: 3px"
        /> Clean Room - No human detected`;

      alarmSound.pause();
    }

    // Update the timestamp
    var timestampElement = document.getElementById("timestamp");
    timestampElement.innerText = `Timestamp : ${data.time_stamp}`;
  });

  socket.on("connect_error", (err) => {
    console.log("Socket Connection Error", err);
    iconWithMsg.innerHTML = `<img
    class="ripple-effect"
    src="static/red-circle.png"
    style="height: 15px; width: 15px; margin-bottom: 3px"
  /> Connection Error!`;
  });

  socket.on("disconnect", () => {
    console.log("Socket disconnected");
  });
};
