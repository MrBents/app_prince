const express = require("express");
const app = express();
var server = require("http").Server(app);
var io = require("socket.io")(server);
const moment = require("moment");
var fs = require("fs");

let data_dir = "./sg_datasets/";

if (!fs.existsSync(data_dir)) {
  fs.mkdirSync(data_dir);
}
var cp = require("child_process");

var spawn = cp.spawn;
var exec = cp.exec;

app.use(express.static("public"));

const port = 3030;
var current_process = null;

var _socket;

io.on("connection", function(socket) {
  _socket = socket;
  _socket.emit("images", {
    image_top: "./images/IMG_2_good.JPEG",
    image_head: "./images/IMG_6_goodhead.JPEG"
  });
});

app.get("/start/:zipper", (req, res) => {
  res.sendStatus(200);
  let type = req.params.zipper;
  console.log(type);
  current_process = spawn("python", [
    "continuous_construction.py",
    req.params.zipper,
    "blue",
    "12"
  ]);

  current_process.stdout.on("data", function(data) {
    console.log(data.toString());
  });

  current_process.stderr.on("data", function(error) {
    _socket.emit("err", { error: error.toString() });
    console.log(error.toString());
  });
});

app.get("/stop", async (req, res) => {
  let type = req.params.zipper;
  current_process.kill();
  res.sendStatus(200);
  let name = moment().format();

  fs.mkdirSync(data_dir + name);

  const { stdout, stderr } = await exec(
    "mv ./public/images/*.jpg " + data_dir + name,
    (err, stdout, stderr) => {
      if (err) {
        // node couldn't execute the command
        return;
      }

      // the *entire* stdout and stderr (buffered)
      console.log(`stdout: ${stdout}`);
      console.log(`stderr: ${stderr}`);
    }
  );
});

app.get("/imgs", (req, res) => {
  _socket.emit("images", {
    image_top: req.query.path_top,
    image_head: req.query.path_head
  });
});

server.listen(port, () =>
  console.log(`Example app listening on port ${port}!`)
);
