<template>

<div class="container">

  <h2>AI Face Recognition</h2>

  <div class="controls">

    <input
      v-model="cameraIp"
      placeholder="http://ip:8080/video"
    />

    <button
      :class="{active:running}"
      @click="start"
    >
      ▶ Start Camera
    </button>

    <button
      class="stop"
      @click="stop"
    >
      ⏹ Stop Camera
    </button>

  </div>

  <div class="video-wrapper">

    <!-- MJPEG STREAM -->
    <img
      ref="video"
      class="video"
    />

    <!-- FACE BOX -->
    <canvas ref="canvas"></canvas>

  </div>

  <div class="info">

    <p>Camera running: {{status.camera_running}}</p>
    <p>Session active: {{status.session_active}}</p>
    <p>Confirmed: {{status.session_confirmed}}</p>
    <p>Distance: {{status.distance}}</p>

  </div>

</div>

</template>


<script setup>

import { ref, onMounted, onBeforeUnmount } from "vue"
import { startCamera, stopCamera, getStatus } from "../services/faceApi"

const cameraIp = ref("http://11.22.88.63:8080/video")

const status = ref({})

const video = ref(null)
const canvas = ref(null)

let ctx = null
let poller = null

const running = ref(false)


/* START CAMERA */

async function start(){

  if(running.value) return

  try{

    await startCamera(cameraIp.value)

    video.value.src = cameraIp.value

    running.value = true

    startPolling()

  }catch(e){

    console.error("Start camera failed",e)

  }

}


/* STOP CAMERA */

async function stop(){

  try{

    await stopCamera()

  }catch(e){
    console.log(e)
  }

  running.value = false

  video.value.src = ""

  stopPolling()

  clearCanvas()

}


/* POLL API */

function startPolling(){

  if(poller) return

  poller = setInterval(updateStatus,200)

}

function stopPolling(){

  clearInterval(poller)

  poller = null

}


/* UPDATE STATUS */

async function updateStatus(){

  try{

    const res = await getStatus()

    status.value = res.data

    drawFace()

  }catch(e){

    console.log("API offline")

  }

}


/* DRAW FACE BOX */

function drawFace(){

  if(!ctx) return

  clearCanvas()

  const face = status.value.face_box
  if(!face) return

  const videoWidth = video.value.clientWidth
  const videoHeight = video.value.clientHeight

  const canvasWidth = canvas.value.width
  const canvasHeight = canvas.value.height

  const scaleX = canvasWidth / 480
  const scaleY = canvasHeight / 480

  ctx.strokeStyle = "#00ff00"
  ctx.lineWidth = 3

  ctx.strokeRect(
    face.left * scaleX,
    face.top * scaleY,
    face.width * scaleX,
    face.height * scaleY
  )

}


/* CLEAR CANVAS */

function clearCanvas(){

  ctx.clearRect(
    0,
    0,
    canvas.value.width,
    canvas.value.height
  )

}


/* INIT */

onMounted(()=>{

  ctx = canvas.value.getContext("2d")

  video.value.onload = ()=>{

    canvas.value.width = video.value.clientWidth
    canvas.value.height = video.value.clientHeight

  }

})


/* CLEANUP */

onBeforeUnmount(()=>{

  stopPolling()

})

</script>



<style>

body{
background:#081b33;
color:white;
font-family:Arial;
}

.container{
width:720px;
margin:auto;
text-align:center;
padding-top:20px;
}

h2{
margin-bottom:20px;
}

.controls{
margin-bottom:20px;
}

input{

width:340px;
padding:10px;
border-radius:6px;
border:none;
margin-right:10px;

}

button{

padding:10px 18px;
border:none;
border-radius:6px;
margin-right:10px;
cursor:pointer;

background:#2196f3;
color:white;

transition:all 0.2s;

}

button:hover{

transform:scale(1.05);
background:#1e88e5;

}

button:active{

transform:scale(0.95);
background:#1565c0;

}

button.active{

background:#2ecc71;

}

button.stop{

background:#e74c3c;

}

button.stop:hover{

background:#c0392b;

}

.video-wrapper{

position:relative;
width:640px;
height:480px;
margin:auto;

border:3px solid #0af;
border-radius:8px;
overflow:hidden;

}

.video{

width:640px;
height:480px;
background:black;

}

canvas{

position:absolute;
left:0;
top:0;
width:640px;
height:480px;

pointer-events:none;

}

.info{

margin-top:20px;
font-size:14px;

}

</style>