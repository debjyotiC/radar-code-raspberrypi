window.onload = function () {
  // Code to be executed when the page is fully loaded
  // console.log("Page loaded");
  var iconWithMsg = document.getElementById("iconWithMsg");
  var alarmSound = document.getElementById("alarmSound");
  var objectLists = document.getElementById("objectLists");
  var noOfObjects = document.getElementById("noOfObjects");
  var showNoSound = document.getElementById("showNoSound");

  showNoSound.innerHTML = `<img
          src="{{ url_for('static', filename='silent-line-icon.png') }}"
          style="height: 15px; width: 15px; margin-bottom: 3px"
        />`;

  showNoSound.addEventListener("click", function () {
    // showNoSound.style.display = "none";
    showNoSound.innerHTML = `<img
          src="{{ url_for('static', filename='volume-line-icon.png') }}"
          style="height: 15px; width: 15px; margin-bottom: 3px"
        />`;
  });

  // Additional actions...
  var socket = io.connect("http://" + document.domain + ":" + location.port);

  socket.on("data", function (data) {
    // console.log("data", JSON.stringify(data));
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
    // Plotly.react(
    //   "plotly-container",
    //   [
    //     {
    //       x: x,
    //       y: y,
    //       z: z,
    //       type: "contour",
    //       colorscale: [
    //         //   ["0.0", "rgb(165,0,38)"],
    //         //   ["0.111111111111", "rgb(215,48,39)"],
    //         //   ["0.222222222222", "rgb(244,109,67)"],
    //         //   ["0.333333333333", "rgb(253,174,97)"],
    //         //   ["0.444444444444", "rgb(254,224,144)"],
    //         //   ["0.555555555556", "rgb(224,243,248)"],
    //         //   ["0.666666666667", "rgb(171,217,233)"],
    //         //   ["0.777777777778", "rgb(116,173,209)"],
    //         //   ["0.888888888889", "rgb(69,117,180)"],
    //         //   ["1.0", "rgb(49,54,149)"],
    //         //   -------------------------------
    //         //   ["0.0", "#33FF00"],
    //         //   ["0.111111111111", "#AA0000"],
    //         //   ["0.222222222222", "#AB0000"],
    //         //   ["0.333333333333", "#BB0000"],
    //         //   ["0.444444444444", "#CB0000"],
    //         //   ["0.555555555556", "#CC0000"],
    //         //   ["0.666666666667", "#CD0000"],
    //         //   ["0.777777777778", "#DD0000"],
    //         //   ["0.888888888889", "#DE0000"],
    //         //   ["1.0", "#FF0000"],
    //         //   ------------------------------
    //         // ["0.0", "#00FF00 "],
    //         // ["0.111111111111", "#33FF00"],
    //         // ["0.222222222222", "#66FF00"],
    //         // ["0.333333333333", "#88FF00"],
    //         // ["0.444444444444", "#CCFF00"],
    //         // ["0.555555555556", "#FFFF00"],
    //         // ["0.666666666667", "#FFCC00"],
    //         // ["0.777777777778", "#FF8800"],
    //         // ["0.888888888889", "#FF4400"],
    //         // ["1.0", "#FF0000"],
    //         // ---------------------------------
    //         // ["0.0", "#440000 "],
    //         // ["0.301029995663981", "#550000"],
    //         // ["0.477121254719662", "#660000"],
    //         // ["0.602059991327962", "#880000"],
    //         // ["0.698970004336018", "#A00000"],
    //         // ["0.778151250383643", "#BB0000"],
    //         // ["0.845098040014256", "#CF0000"],
    //         // ["0.903089986991943", "#EF0000"],
    //         // ["0.954242509439324", "#FF0000"],
    //         // ["1.0", "#FFF000"],
    //         // --------------------------------
    //         ["0.0", "#99FF00 "],
    //         ["0.301029995663981", "#88FF00"],
    //         ["0.477121254719662", "#77FF00"],
    //         ["0.602059991327962", "#66FF00"],
    //         ["0.698970004336018", "#55FF00"],
    //         ["0.778151250383643", "#44FF00"],
    //         ["0.845098040014256", "#33FF00"],
    //         ["0.903089986991943", "#22FF00"],
    //         ["0.954242509439324", "#11FF00"],
    //         ["1.0", "#00FF00"],
    //       ],
    //       contours: {
    //         showlines: false,
    //         smooth: true,
    //       },
    //       showscale: false,
    //     },
    //   ],
    //   layout
    // );

    let noOfObject = Math.floor(Math.random() * 15) + 1;
    noOfObjects.innerText = `No of Object detected : ${noOfObject}`;

    let objectListsHtml = ``;
    for (let i = 0; i < noOfObject; i++) {
      objectListsHtml += `<div class="message">
                    <div class="message-content">Object: ${
                      Math.floor(Math.random() * 20) + 1
                    }, Distance: ${
        Math.floor(Math.random() * 100) + 1
      } ft.</div>
                  </div>`;
    }
    objectLists.innerHTML = objectListsHtml;

    // Set the box color based on the classification
    if (classification === "occupied_room") {
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
          src="{{ url_for('static', filename='red-circle-icon.png') }}"
          style="height: 15px; width: 15px; margin-bottom: 3px"
        /> Room Occupied`;
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
              ["0.0", "#99FF00 "],
              ["0.301029995663981", "#88FF00"],
              ["0.477121254719662", "#77FF00"],
              ["0.602059991327962", "#66FF00"],
              ["0.698970004336018", "#55FF00"],
              ["0.778151250383643", "#44FF00"],
              ["0.845098040014256", "#33FF00"],
              ["0.903089986991943", "#22FF00"],
              ["0.954242509439324", "#11FF00"],
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
          src="{{ url_for('static', filename='green-circle-icon.png') }}"
          style="height: 15px; width: 15px; margin-bottom: 3px"
        /> Room Free`;

      alarmSound.pause();
    }

    // Update the timestamp
    var timestampElement = document.getElementById("timestamp");
    timestampElement.innerText = `Timestamp : ${new Date().toLocaleString()}`;
  });

  socket.on("connect_error", (err) => {
    console.log("Socket Connection Error", err);
    iconWithMsg.innerHTML = `<i
                class="fa fa-sharp fa-solid fa-circle ripple-effect"
                style="color: red"
              ></i> Connection Error`;
  });

  socket.on("disconnect", () => {
    console.log("Socket disconnected");
  });
};
