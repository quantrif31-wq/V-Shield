<template>

<div class="console">

<header class="topbar">

<div class="title">
V-Shield AI Security Console
</div>

<div class="system-status">
<span class="led" :class="{on:faceRunning || plateRunning}"></span>
{{ faceRunning || plateRunning ? "AI SYSTEM ONLINE" : "AI SYSTEM OFFLINE" }}
</div>

</header>


<div class="layout">

<!-- CONTROL PANEL -->

<div class="control">

<h3>FACE CAMERA</h3>

<input v-model="faceCameraIp" placeholder="Face camera URL"/>

<button class="btn start" @click="startFace">
START FACE
</button>

<button class="btn stop" @click="stopFace">
STOP FACE
</button>

<hr>

<h3>PLATE CAMERA</h3>

<select v-model="selectedCamera" @change="connectPlate">

<option value="">Select Camera</option>

<option
v-for="cam in cameras"
:key="cam.cameraIP"
:value="cam.cameraIP"
>
{{ cam.cameraIP }}
</option>

</select>

<button class="btn stop" @click="stopPlate">
STOP PLATE
</button>

</div>


<!-- CAMERA PANEL -->

<div class="camera-panel">

<!-- FACE CAMERA -->

<div class="video-wrapper">

<img
ref="faceVideo"
class="video"
:style="{ transform: FACE_TRANSFORM }"
/>

<canvas
ref="faceCanvas"
:style="{ transform: FACE_TRANSFORM }"
></canvas>

<div class="overlay">

<div>FACE DETECTION</div>

<div>Status : {{detectLabel}}</div>
<div>Gate : {{gateStatus}}</div>

<div v-if="status.employee_id">
Employee : {{status.employee_id}}
</div>

<div>Distance : {{status.distance}}</div>

<div v-if="status.session_confirmed" class="confirm">
✔ IDENTIFIED
</div>

</div>

</div>


<!-- PLATE CAMERA -->

<div class="video-wrapper">

<img
v-if="plateRunning"
:src="streamUrl"
class="video"
ref="plateVideo"
:style="{ transform: PLATE_TRANSFORM }"
/>

<canvas
ref="plateCanvas"
:style="{ transform: PLATE_TRANSFORM }"
></canvas>
<div class="overlay">

<div>LICENSE PLATE</div>

<div>Plate : {{ plate || "-----" }}</div>

</div>

</div>

<div class="plate-big">
{{ plate || "-----" }}
</div>

</div>

</div>

</div>

</template>


<script setup>

import {ref,onMounted,onBeforeUnmount,computed} from "vue"

import {
startCamera,
stopCamera,
getStatus
} from "../services/faceApi"

import {
getCameras,
getPlate
} from "../services/biensoApi"
import { scanGate } from "../services/thonghanhAPI"


/* STATE */
const FACE_TRANSFORM = "rotate(-90deg) scaleX(-1)"   // cam trước
const PLATE_TRANSFORM = "rotate(0deg)"              // cam sau
const cameras = ref([])
const selectedCamera = ref("")

const faceCameraIp = ref("http://127.0.0.1:8080/video")

const plate = ref("")
const status = ref({})

const faceRunning = ref(false)
const plateRunning = ref(false)

const streamUrl = ref("")

const faceVideo = ref(null)
const plateVideo = ref(null)

const faceCanvas = ref(null)
const plateCanvas = ref(null)

let faceCtx=null
let plateCtx=null

let faceLoop=null
let plateLoop=null
let gateLoop=null

const gateStatus = ref("")

/* FACE LABEL */

const detectLabel = computed(()=>{

if(!status.value.session_active) return "IDLE"
if(status.value.session_confirmed) return "IDENTIFIED"
if(status.value.face_match) return "VERIFYING"

return "UNKNOWN"

})


/* LOAD CAMERAS */

async function loadCameras(){

try{

const res = await getCameras()

cameras.value = res || []

}catch(e){

console.log("camera load error")

}

}


/* FACE START */

async function startFace(){

await startCamera(faceCameraIp.value)

faceVideo.value.src = faceCameraIp.value

faceRunning.value=true

startFaceLoop()

}


async function stopFace(){

await stopCamera()

faceRunning.value=false

clearInterval(faceLoop)

faceVideo.value.src=""

clearFace()

}


/* FACE LOOP */

function startFaceLoop(){

clearInterval(faceLoop)

faceLoop=setInterval(updateFace,300)

}


async function updateFace(){

if(!faceRunning.value) return

try{

const res = await getStatus()

status.value = res.data || {}

drawFace()

}catch(e){

console.log("face error")

}

}


function drawFace(){

if(!faceCtx) return

clearFace()

const face=status.value.face_box

if(!face) return

const scaleX = faceCanvas.value.width/480
const scaleY = faceCanvas.value.height/480

faceCtx.strokeStyle="#00ff9c"
faceCtx.lineWidth=3

const x = faceCanvas.value.width - (face.left + face.width) * scaleX

faceCtx.strokeRect(
x,
face.top * scaleY,
face.width * scaleX,
face.height * scaleY
)

}


function clearFace(){

faceCtx.clearRect(
0,
0,
faceCanvas.value.width,
faceCanvas.value.height
)

}


/* PLATE CONNECT */

function connectPlate(){

if(!selectedCamera.value) return

streamUrl.value = selectedCamera.value

plateRunning.value=true

startPlateLoop()

}


function stopPlate(){

plateRunning.value=false

clearInterval(plateLoop)

plate.value=""

if(plateCtx && plateCanvas.value){
  plateCtx.clearRect(
    0,
    0,
    plateCanvas.value.width,
    plateCanvas.value.height
  )
}

}


/* PLATE LOOP */

function startPlateLoop(){

clearInterval(plateLoop)

plateLoop=setInterval(updatePlate,500)

}


async function updatePlate(){

if(!plateRunning.value) return

try{

const res = await getPlate(selectedCamera.value)

if(!res) return

plate.value = res.plateNumber

drawPlate(res)

}catch(e){

console.log("plate error")

}

}


function drawPlate(res){

const canvas=plateCanvas.value
const img=plateVideo.value

if(!canvas || !img) return

canvas.width=img.clientWidth
canvas.height=img.clientHeight

plateCtx.clearRect(0,0,canvas.width,canvas.height)

const scaleX=canvas.width/640
const scaleY=canvas.height/360

const x=res.x1*scaleX
const y=res.y1*scaleY
const w=(res.x2-res.x1)*scaleX
const h=(res.y2-res.y1)*scaleY

plateCtx.strokeStyle="#00ff00"
plateCtx.lineWidth=3

plateCtx.strokeRect(x,y,w,h)

plateCtx.font="20px Arial"
plateCtx.fillStyle="#00ff00"

plateCtx.fillText(res.plateNumber,x,y-10)

}

async function runGate(){

  try{

    const res = await scanGate()

    if(!res || !res.data) return

    gateStatus.value = res.data.status

    if(res.data.status === "SUCCESS"){
        console.log("OPEN GATE")
    }

  }catch(e){

    console.log("gate error")

  }

}
function startGateLoop(){

  clearInterval(gateLoop)

  gateLoop = setInterval(runGate,1000)

}
/* INIT */

onMounted(()=>{

loadCameras()

faceCtx=faceCanvas.value.getContext("2d")
plateCtx=plateCanvas.value.getContext("2d")
startGateLoop()
faceVideo.value.onload = () => {

const w = faceVideo.value.clientWidth
const h = faceVideo.value.clientHeight

// vì rotate 90 độ → đảo lại
faceCanvas.value.width = h
faceCanvas.value.height = w

}


})


onBeforeUnmount(()=>{

clearInterval(faceLoop)
clearInterval(plateLoop)
clearInterval(gateLoop)
})

</script>


<style>

body{
margin:0;
background:#041424;
color:white;
font-family:Segoe UI;
}

.topbar{
display:flex;
justify-content:space-between;
padding:20px 40px;
background:#0b223f;
}

.title{
font-size:22px;
font-weight:bold;
}

.layout{
display:grid;
grid-template-columns:260px 720px;
gap:30px;
justify-content:center;
padding:30px;
}

.control{
background:#0c2747;
padding:20px;
border-radius:8px;
}

.control select,
.control input{
width:100%;
padding:10px;
margin-bottom:10px;
}

.btn{
width:100%;
padding:12px;
margin-bottom:10px;
border:none;
border-radius:6px;
font-weight:bold;
cursor:pointer;
}

.start{background:#27ae60}
.stop{background:#e74c3c}

.video-wrapper{
position:relative;
width:720px;
height:320px;
background:black;
margin-bottom:20px;
}

.video{
width:100%;
height:100%;
object-fit:contain;
transform-origin:center;
}

canvas{
position:absolute;
top:0;
left:0;
width:100%;
height:100%;
pointer-events:none;
transform-origin:center;
}

.overlay{
position:absolute;
top:10px;
left:10px;
background:rgba(0,0,0,0.5);
padding:8px 12px;
border-radius:6px;
}

.plate-big{
font-size:50px;
text-align:center;
color:#00ff9c;
font-weight:bold;
}

.confirm{
color:#00ff9c;
}

</style>