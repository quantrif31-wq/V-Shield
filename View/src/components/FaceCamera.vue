<template>

<div class="console">

<header class="topbar">

<div class="title">
V-Shield AI Security Console
</div>

<div class="system-status">
<span class="led" :class="{on:running}"></span>
{{ running ? "AI SYSTEM ONLINE" : "AI SYSTEM OFFLINE" }}
</div>

</header>


<div class="layout">

<!-- CONTROL PANEL -->
<div class="control">

<h3>Camera Control</h3>

<input
v-model="cameraIp"
placeholder="Camera Stream URL"
/>

<button class="btn start" @click="start">
▶ START CAMERA
</button>

<button class="btn stop" @click="stop">
■ STOP CAMERA
</button>

<button class="btn shutdown" @click="shutdown">
⚡ SHUTDOWN AI
</button>

</div>


<!-- CAMERA -->
<div class="camera-panel">

<div
class="video-wrapper"
:style="{ '--camColor': detectColor }"
>

<img
ref="video"
class="video"
/>

<canvas ref="canvas"></canvas>

<div class="overlay">

<div :style="{color:detectColor}">
AI FACE DETECTION
</div>

<div>Status : {{detectLabel}}</div>

<div>Distance : {{status.distance}}</div>

<div v-if="status.session_confirmed" class="confirm">
✔ IDENTIFIED
</div>

</div>

</div>

</div>


<!-- STATUS -->
<div class="status">

<h3>Detection Status</h3>

<div class="status-box">

<div class="item">
<span>Camera</span>
<b :class="status.camera_running?'ok':'bad'">
{{status.camera_running ? "ONLINE":"OFFLINE"}}
</b>
</div>

<div class="item">
<span>Session</span>
<b :class="status.session_active?'ok':'bad'">
{{status.session_active}}
</b>
</div>

<div class="item">
<span>Confirmed</span>
<b :class="status.session_confirmed?'ok':'bad'">
{{status.session_confirmed}}
</b>
</div>

<div class="item">
<span>Distance</span>
<b>{{status.distance}}</b>
</div>

</div>

</div>

</div>

</div>

</template>

<script setup>

import {ref,onMounted,onBeforeUnmount,computed} from "vue"
import {startCamera,stopCamera,getStatus,shutdownAI} from "../services/faceApi"

const cameraIp = ref("http://55.247.111.137:8080/video")

const status = ref({})

const video = ref(null)
const canvas = ref(null)

let ctx = null
let poller = null

const running = ref(false)


/* ================= COLOR LOGIC ================= */

const detectColor = computed(()=>{

if(!status.value.session_active)
return "#00bfff"   // idle

if(status.value.session_confirmed)
return "#00ff9c"   // confirmed

if(status.value.face_match)
return "#33ccff"   // verifying

return "#ffd500"   // unknown

})


const detectLabel = computed(()=>{

if(!status.value.session_active)
return "IDLE"

if(status.value.session_confirmed)
return "IDENTIFIED"

if(status.value.face_match)
return "VERIFYING"

return "UNKNOWN"

})


/* ================= CAMERA CONTROL ================= */

async function start(){

if(running.value) return

try{

await startCamera(cameraIp.value)

video.value.src = cameraIp.value

running.value = true

startPolling()

}catch(e){

console.log("start failed",e)

}

}


async function stop(){

try{
await stopCamera()
}catch(e){}

running.value=false

video.value.src=""

stopPolling()

clearCanvas()

}


async function shutdown(){

if(!confirm("Shutdown AI server ?")) return

try{

await shutdownAI()

}catch(e){}

running.value=false

video.value.src=""

stopPolling()

clearCanvas()

}


/* ================= POLLING ================= */

function startPolling(){

if(poller) return

poller=setInterval(updateStatus,200)

}

function stopPolling(){

clearInterval(poller)

poller=null

}


async function updateStatus(){

try{

const res = await getStatus()

status.value = res.data

drawFace()

}catch(e){

running.value=false

}

}


/* ================= DRAW FACE ================= */

function drawFace(){

if(!ctx) return

clearCanvas()

const face = status.value.face_box

if(!face) return

const scaleX = canvas.value.width / 480
const scaleY = canvas.value.height / 480

ctx.strokeStyle = detectColor.value
ctx.lineWidth=3

ctx.strokeRect(
face.left * scaleX,
face.top * scaleY,
face.width * scaleX,
face.height * scaleY
)

}


function clearCanvas(){

ctx.clearRect(
0,
0,
canvas.value.width,
canvas.value.height
)

}


/* ================= INIT ================= */

onMounted(()=>{

ctx = canvas.value.getContext("2d")

video.value.onload = ()=>{

canvas.value.width = video.value.clientWidth
canvas.value.height = video.value.clientHeight

}

})

onBeforeUnmount(()=>{

stopPolling()

})

</script>


<style>

body{
margin:0;
background:#041424;
color:white;
font-family:Segoe UI;
}


/* TOP BAR */

.topbar{

display:flex;
justify-content:space-between;
align-items:center;

padding:20px 40px;

background:#0b223f;
border-bottom:2px solid #0af;

}

.title{
font-size:22px;
font-weight:bold;
letter-spacing:2px;
}


/* LED */

.system-status{

display:flex;
align-items:center;
gap:10px;
font-size:14px;

}

.led{

width:12px;
height:12px;

border-radius:50%;

background:#666;

}

.led.on{

background:#00ff9c;
box-shadow:0 0 12px #00ff9c;

}


/* LAYOUT */

.layout{

display:grid;

grid-template-columns:260px 720px 260px;

gap:30px;

justify-content:center;

padding:30px;

}


/* CONTROL */

.control{

background:#0c2747;
padding:20px;
border-radius:8px;

}

.control input{

width:100%;
padding:10px;
margin-bottom:15px;

border:none;
border-radius:6px;

}


/* BUTTON */

.btn{

width:100%;
padding:12px;

margin-bottom:10px;

border:none;
border-radius:6px;

font-weight:bold;

cursor:pointer;

transition:0.2s;

}

.btn:hover{
transform:scale(1.05)
}

.start{background:#27ae60}
.stop{background:#e74c3c}
.shutdown{background:#f39c12}


/* VIDEO */

.video-wrapper{

position:relative;

width:720px;
height:480px;

border:3px solid var(--camColor);

border-radius:8px;

overflow:hidden;

box-shadow:0 0 20px var(--camColor);

background:black;

}

.video{

position:absolute;

width:100%;
height:100%;

object-fit:contain;

transform: rotate(-90deg);

}

canvas{

position:absolute;

width:100%;
height:100%;

pointer-events:none;

transform: rotate(-90deg);

}

.video,
canvas{
transform: rotate(-90deg) scale(1.5);
transform-origin:center;
}
/* OVERLAY */

.overlay{

position:absolute;

top:10px;
left:10px;

background:rgba(0,0,0,0.5);

padding:8px 12px;

border-radius:6px;

font-size:13px;

border:1px solid #00bfff;

}

.confirm{

color:#00ff9c;
font-weight:bold;

}


/* STATUS */

.status{

background:#0c2747;
padding:20px;
border-radius:8px;

}

.status-box{

margin-top:15px;

display:flex;
flex-direction:column;
gap:10px;

}

.item{

display:flex;
justify-content:space-between;

padding:10px;

background:#081b33;

border-radius:6px;

}

.ok{color:#00ff9c}
.bad{color:#ff5a5a}

</style>