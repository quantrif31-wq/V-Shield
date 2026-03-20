<template>

<div class="console">

<header class="topbar">

<div class="title">
V-Shield AI Security Console
</div>
<div v-if="alarmActive" class="alarm-overlay">
🚨 SECURITY ALERT 🚨
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
<button class="btn shutdown" @click="shutdown">
⚡ SHUTDOWN AI
</button>
<button
v-if="alarmActive"
class="btn stop"
@click="stopAlarm"
>
🧯 STOP ALARM
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

  <!-- FACE -->
  <div class="video-wrapper"
       :class="{
         'success-glow': status.session_confirmed,
         'alert-glow': alarmActive
       }"
       :style="{ '--camColor': detectColor }">

    <img ref="faceVideo" class="video"
         :style="{ transform: FACE_TRANSFORM }"/>

    <canvas ref="faceCanvas"
            :style="{ transform: FACE_TRANSFORM }"></canvas>

    <!-- NEW OVERLAY -->
    <div class="overlay">

  <!-- HEADER -->
  <div class="row space">
    <div>
      <div class="label">STATUS</div>
      <div class="value">{{ detectLabel }}</div>
    </div>

    <div>
      <div class="label">GATE</div>
      <div class="value">{{ gateStatus }}</div>
    </div>
  </div>

  <!-- MESSAGE -->
  <div class="main-message" :style="{ color: messageColor }">
  {{ gateMessage }}
</div>

  <!-- DATA GRID -->
  <div class="grid">
  <div><span class="g-label">ID:</span> {{ displayId }}</div>
  <div><span class="g-label">Plate:</span> {{ displayPlate }}</div>
  <div><span class="g-label">Parking:</span> {{ displayParking }}</div>
  <div><span class="g-label">Dist:</span> {{ displayDistance }}</div>
</div>

  <!-- BADGE -->
  <div class="badge success" v-if="status.session_confirmed">
    ✔ IDENTIFIED
  </div>

</div>

  </div>

  <!-- PLATE -->
  <div class="video-wrapper">

    <img v-if="plateRunning"
         :src="streamUrl"
         class="video"
         ref="plateVideo"
         :style="{ transform: PLATE_TRANSFORM }"/>

    <canvas ref="plateCanvas"
            :style="{ transform: PLATE_TRANSFORM }"></canvas>

    <div class="overlay">
      <div class="status-line">
        <span class="label">PLATE</span>
        <span class="value">{{ plate || "-----" }}</span>
      </div>
    </div>

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
//getCameras,
//getPlate
} from "../services/biensoApi"
import { scanGate } from "../services/thonghanhAPI"
import { shutdownAI } from "../services/faceApi"

/* STATE */
const FACE_TRANSFORM = "rotate(-90deg)"   // cam trước
const PLATE_TRANSFORM = "rotate(0deg)"              // cam sau
const cameras = ref([])
const selectedCamera = ref("")

const faceCameraIp = ref("http://127.0.0.1:8080/video")
const alarmActive = ref(false)
let lastConfirmed = false
let gateLoop = null
const successSound = new Audio("/sounds/success.mp3")
const alarmSound = new Audio("/sounds/alarm.mp3")

alarmSound.loop = true
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

let gateLocked = false  // 🔒 chỉ cho phép SUCCESS 1 lần mỗi session

const gateStatus = ref("")
const gateResult = ref(null)   // lưu toàn bộ response scan
const gateMessage = ref("")    // text hiển thị

function stopAlarm(){

alarmActive.value = false

alarmSound.pause()
alarmSound.currentTime = 0

startFaceLoop() // chạy lại face loop

}
/* FACE LABEL */

const detectLabel = computed(()=>{

if(!status.value.session_active) return "IDLE"
if(status.value.session_confirmed) return "IDENTIFIED"
if(status.value.face_match) return "VERIFYING"

return "UNKNOWN"

})
const detectColor = computed(()=>{

if(!status.value.session_active)
return "#00bfff"

if(status.value.session_confirmed)
return "#00ff9c"

if(status.value.face_match)
return "#33ccff"

return "#ffd500"

})
const displayId = computed(()=>{
  return (
    gateResult.value?.employeeId ||
    status.value?.employee_id ||
    "-"
  )
})

const displayPlate = computed(()=>{
  return (
    gateResult.value?.plate ||
    plate.value ||
    status.value?.plate ||
    "-"
  )
})

const displayParking = computed(()=>{
  return (
    gateResult.value?.parkingStatus ||
    status.value?.parking_status ||
    "-"
  )
})

const displayDistance = computed(()=>{
  const d = status.value.distance
  if(!d) return "-"
  return Number(d).toFixed(2) + "m"
})

const messageColor = computed(()=>{
  switch(gateStatus.value){
    case "SUCCESS": return "#00ff9c"
    case "WAIT_PLATE": return "#ffd500"
    case "WAIT_FACE": return "#00bfff"
    case "NO_EMPLOYEE": return "red"
    default: return "#ccc"
  }
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

async function shutdown(){

if(!confirm("Shutdown AI server ?")) return

try{
await shutdownAI()
}catch(e){}

faceRunning.value=false
faceVideo.value.src=""

clearInterval(faceLoop)
clearFace()

}

/* FACE LOOP */

function startFaceLoop(){

clearInterval(faceLoop)

faceLoop=setInterval(updateFace,300)

}


async function updateFace(){
if(alarmActive.value) return
if(!faceRunning.value) return

try{

const res = await getStatus()

status.value = res.data || {}
// 🔓 reset khi session kết thúc
if(!status.value.session_active){
    gateLocked = false
}

// ===== SUCCESS SOUND =====
if(
    status.value.session_confirmed &&
    !lastConfirmed
){
    successSound.currentTime = 0
    successSound.play()
}

lastConfirmed = status.value.session_confirmed


// ===== ALARM =====
if(status.value.alert && !alarmActive.value){






















































































































































































































































    alarmActive.value = true

    alarmSound.currentTime = 0
    alarmSound.play()

    clearInterval(faceLoop) // ⛔ stop face loop
}

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
if(gateLocked) return  // 🔒 đã SUCCESS thì không gọi nữa
  try{

    const res = await scanGate()

    if(!res || !res.data) return

    const data = res.data

    gateResult.value = data
    gateStatus.value = data.status

    // =========================
    // XỬ LÝ UI THEO STATUS
    // =========================

    switch(data.status){

      case "WAIT_FACE":
        gateMessage.value = "🟡 Waiting for face..."
        break

      case "WAIT_PLATE":
        gateMessage.value = "🟡 Waiting for plate..."
        break

      case "NO_EMPLOYEE":
        gateMessage.value = "❌ Unknown employee"
        
        alarmSound.currentTime = 0
        alarmSound.play()
        break

      case "SUCCESS":

        gateMessage.value = `✅ ${data.action} | Plate: ${data.plate}`

        successSound.currentTime = 0
        successSound.play()

        gateLocked = true   // 🔥 KHÓA SAU KHI THÀNH CÔNG

        console.log("OPEN GATE", data)

        break

        gateMessage.value = `✅ ${data.action} | Plate: ${data.plate}`

        // 🔊 mở cổng sound
        successSound.currentTime = 0
        successSound.play()

        console.log("OPEN GATE", data)

        break

      default:
        gateMessage.value = data.status
    }

  }catch(e){

    console.log("gate error")

  }

}
function startGateLoop(){

  clearInterval(gateLoop)

  gateLoop = setInterval(() => {
    runGate()
  }, 1000)

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
grid-template-columns:280px 1fr;
height:calc(100vh - 80px);
gap:16px;
padding:16px;
}

.control{
background:#0c2747;
padding:16px;
border-radius:8px;
border-right:1px solid rgba(255,255,255,0.1);
}

.control select,
.control input{
width:100%;
padding:10px;
margin-bottom:10px;
}

.btn{
width:100%;
padding:10px;
margin-bottom:8px;
font-size:13px;
border:none;
border-radius:6px;
font-weight:bold;
cursor:pointer;
}

.start{background:#27ae60}
.stop{background:#e74c3c}

.video-wrapper{
position:relative;
border-radius:12px;
overflow:hidden;
background:black;
border:2px solid var(--camColor);
box-shadow:0 0 10px var(--camColor);
transition:0.3s;
}

.video{
width:100%;
height:100%;
object-fit:cover;
max-height:100%;
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

  min-width:240px;
  max-width:320px;   /* 🔥 FIX CỤT */

  background:rgba(0,0,0,0.8);
  padding:10px;
  border-radius:8px;

  font-size:13px;
}
/* STATUS ROW */
.top-row{
  display:flex;
  justify-content:space-between;
  margin-bottom:6px;
}

.status-box{
  text-align:left;
}

.label{
  font-size:11px;
  color:#aaa;
}

.value{
  font-weight:bold;
  font-size:14px;
}

/* MESSAGE */
.main-message{
  font-weight:bold;
  font-size:14px;
  margin:4px 0;
  color:#00ff9c;
}

/* GRID INFO */
.info-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:4px;
  font-size:12px;
  color:#ddd;
}

/* BADGES */
.badges{
  margin-top:6px;
  display:flex;
  gap:6px;
}

.badge{
  padding:2px 6px;
  border-radius:4px;
  font-size:11px;
  font-weight:bold;
}

.badge.success{
  background:#00ff9c;
  color:black;
}

.badge.alert{
  background:red;
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
.camera-panel{
display:grid;
grid-template-rows: 2fr 1fr;
gap:16px;
height:100%;
}

.success-glow{
box-shadow:0 0 30px #00ff9c !important;
border-color:#00ff9c !important;
}

.alert-glow{
box-shadow:0 0 40px red !important;
border-color:red !important;
}
.status-line{
display:flex;
justify-content:space-between;
margin-bottom:4px;
}

.label{
color:#aaa;
}

.value{
font-weight:bold;
}

.main-message{
margin-top:6px;
font-size:16px;
font-weight:bold;
}
.alarm-overlay{
position:fixed;
top:0;
left:0;
right:0;
bottom:0;
background:rgba(255,0,0,0.2);
display:flex;
justify-content:center;
align-items:center;
font-size:48px;
font-weight:bold;
color:red;
z-index:999;
animation: blink 1s infinite;
}

@keyframes blink{
0%{opacity:1}
50%{opacity:0.4}
100%{opacity:1}
}
.camera-panel{
display:grid;
grid-template-rows: 2fr 1fr;
gap:16px;
height:100%;

}
.video-wrapper{
height:100%;
}
.control{
overflow:auto;
}
.row{
  display:flex;
}

.space{
  justify-content:space-between;
  margin-bottom:6px;
}

.label{
  font-size:11px;
  color:#bbbbbb;   /* 🔥 từ #aaa → sáng hơn */
  letter-spacing:0.5px;
}

.value{
  font-weight:bold;
}

.main-message{
  margin:4px 0;
  font-weight:bold;
  color:#00ff9c;
}

.grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:4px;
  font-size:12px;
}

.badge{
  margin-top:6px;
  padding:3px 6px;
  font-size:11px;
  border-radius:4px;
  display:inline-block;
}

.badge.success{
  background:#00ff9c;
  color:black;
}
.value{
  font-weight:bold;
  font-size:15px;
  color:#ffffff;   /* 🔥 trắng hẳn */
}
.main-message{
  margin:6px 0;
  font-size:15px;
  font-weight:bold;
}
.grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:6px;
  font-size:12px;
  color:#ddd;
}
.g-label{
  color:#66ccff;   /* 🔥 xanh nhẹ dễ đọc */
  margin-right:4px;
}
.main-message{
  margin:6px 0;
  font-size:16px;
  font-weight:bold;
  text-shadow:0 0 6px rgba(255,255,255,0.3); /* 🔥 glow nhẹ */
}
.value{
  font-weight:bold;
  font-size:15px;
}

.row .value{
  font-size:16px;
}
.grid div:nth-child(2){
  color:#00ff9c;
  font-weight:bold;
}
.success-glow .overlay{
  background:rgba(0,50,0,0.75);
}
</style>