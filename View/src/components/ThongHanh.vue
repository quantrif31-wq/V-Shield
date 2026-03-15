<template>

<div class="monitor">

<h1>V-Shield AI Gate Monitor</h1>

<div class="inputs">

<input v-model="faceIp" placeholder="Face Camera IP"/>

<input v-model="plateIp" placeholder="Plate Camera IP"/>

<button @click="start">START</button>

</div>

<div class="cams">

<!-- FACE CAMERA -->

<div class="cam">

<h3>FACE CAMERA</h3>

<div class="video-wrapper">

<img ref="faceVideo" class="video"/>

<canvas ref="faceCanvas"></canvas>

</div>

<div class="info">

<div>Status : {{faceLabel}}</div>

<div v-if="face.employee_id">
Employee : {{face.employee_id}}
</div>

</div>

</div>


<!-- PLATE CAMERA -->

<div class="cam">

<h3>PLATE CAMERA</h3>

<div class="video-wrapper">

<img
:src="plateIp"
class="video"
ref="plateVideo"
/>

<canvas ref="plateCanvas"></canvas>

</div>

<div class="plate">

{{plate || "-----"}}

</div>

</div>

</div>

</div>

</template>
<script setup>

import {ref,onMounted,onBeforeUnmount,computed} from "vue"
import {getStatus} from "../services/faceApi"
import {getPlate} from "../services/biensoApi"

const faceIp = ref("")
const plateIp = ref("")

const face = ref({})
const plate = ref(null)

const faceVideo = ref(null)
const plateVideo = ref(null)

const faceCanvas = ref(null)
const plateCanvas = ref(null)

let faceCtx = null
let plateCtx = null

let poller = null


/* ================= FACE COLOR ================= */

const faceColor = computed(()=>{

if(!face.value.session_active)
return "yellow"

if(face.value.session_confirmed)
return "#00ff00"

return "yellow"

})

const faceLabel = computed(()=>{

if(!face.value.session_active)
return "IDLE"

if(face.value.session_confirmed)
return "CONFIRMED"

return "DETECTING"

})


/* ================= START ================= */

function start(){

faceVideo.value.src = faceIp.value

startPolling()

}


/* ================= POLLING ================= */

function startPolling(){

poller = setInterval(update,300)

}


function stopPolling(){

clearInterval(poller)

}


/* ================= UPDATE ================= */

async function update(){

try{

const resFace = await getStatus()

face.value = resFace.data

drawFace()


const resPlate = await getPlate()

plate.value = resPlate.plateNumber

drawPlate(resPlate)

}catch(e){

console.log("poll error")

}

}


/* ================= DRAW FACE ================= */

function drawFace(){

const ctx = faceCtx
const canvas = faceCanvas.value

ctx.clearRect(0,0,canvas.width,canvas.height)

const box = face.value.face_box

if(!box) return

const scaleX = canvas.width / 480
const scaleY = canvas.height / 480

ctx.strokeStyle = faceColor.value
ctx.lineWidth = 3

ctx.strokeRect(

box.left * scaleX,
box.top * scaleY,
box.width * scaleX,
box.height * scaleY

)

}


/* ================= DRAW PLATE ================= */

function drawPlate(res){

const ctx = plateCtx
const canvas = plateCanvas.value

ctx.clearRect(0,0,canvas.width,canvas.height)

if(!res) return

const scaleX = canvas.width / 640
const scaleY = canvas.height / 360

const x = res.x1 * scaleX
const y = res.y1 * scaleY
const w = (res.x2-res.x1) * scaleX
const h = (res.y2-res.y1) * scaleY

ctx.strokeStyle="#00ff00"
ctx.lineWidth=3

ctx.strokeRect(x,y,w,h)

ctx.font="20px Arial"
ctx.fillStyle="#00ff00"

ctx.fillText(res.plateNumber,x,y-10)

}


/* ================= INIT ================= */

onMounted(()=>{

faceCtx = faceCanvas.value.getContext("2d")
plateCtx = plateCanvas.value.getContext("2d")

faceVideo.value.onload = ()=>{

faceCanvas.value.width = faceVideo.value.clientWidth
faceCanvas.value.height = faceVideo.value.clientHeight

}

plateVideo.value.onload = ()=>{

plateCanvas.value.width = plateVideo.value.clientWidth
plateCanvas.value.height = plateVideo.value.clientHeight

}

})


onBeforeUnmount(()=>{

stopPolling()

})

</script>
<style scoped>

.monitor{
width:1200px;
margin:auto;
color:white;
text-align:center;
}

.cams{
display:flex;
gap:40px;
justify-content:center;
margin-top:20px;
}

.cam{
width:520px;
}

.video-wrapper{
position:relative;
width:520px;
height:360px;
background:black;
}

.video{
width:100%;
height:100%;
object-fit:contain;
}

canvas{
position:absolute;
top:0;
left:0;
width:100%;
height:100%;
pointer-events:none;
}

.plate{
font-size:40px;
color:#00ff00;
margin-top:10px;
font-weight:bold;
}

</style>