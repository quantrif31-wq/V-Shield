<template>

<div class="security-container">

<h1 class="title">Gate Camera Monitor</h1>

<select v-model="selectedCamera" @change="connectCamera">

<option value="">Select Camera</option>

<option
v-for="cam in cameras"
:key="cam.cameraIP"
:value="cam.cameraIP"
>
{{ cam.cameraIP }}
</option>

</select>

<div class="video-wrapper">

<img
v-if="cameraRunning"
:src="streamUrl"
class="video"
ref="video"
/>

<canvas
ref="canvas"
class="overlay"
></canvas>

<div v-if="!cameraRunning" class="video-off">
Camera Offline
</div>

</div>

<div class="plate-panel">

<div class="plate-label">Detected Plate</div>

<div class="plate-number">
{{ plate || "-----" }}
</div>

</div>

</div>

</template>


<script>

import { getCameras,getPlate } from "../services/biensoApi"

export default{

name:"SecurityPlateMonitor",

data(){

return{

cameras:[],
selectedCamera:"",

streamUrl:"",
cameraRunning:false,

plate:"",

pollTimer:null

}

},

async mounted(){

await this.loadCameras()

},

methods:{

async loadCameras(){

try{

const data = await getCameras()

console.log("CAMERAS:",data)

this.cameras = data

}
catch(e){

console.error("Load camera error",e)

}

},

connectCamera(){

if(!this.selectedCamera) return

this.streamUrl = this.selectedCamera

this.cameraRunning = true

this.startPolling()

},

startPolling(){

if(this.pollTimer)
clearInterval(this.pollTimer)

this.pollTimer = setInterval(async()=>{

try{

const res = await getPlate(this.selectedCamera)

if(!res) return

this.plate = res.plateNumber

this.drawBox(res)

}
catch(e){

console.log("poll error")

}

},500)

},

drawBox(res){

const canvas = this.$refs.canvas
const ctx = canvas.getContext("2d")
const img = this.$refs.video

if(!img) return

canvas.width = img.clientWidth
canvas.height = img.clientHeight

ctx.clearRect(0,0,canvas.width,canvas.height)

if(!res) return

const scaleX = canvas.width / 640
const scaleY = canvas.height / 360

const x = res.x1 * scaleX
const y = res.y1 * scaleY
const w = (res.x2 - res.x1) * scaleX
const h = (res.y2 - res.y1) * scaleY

ctx.strokeStyle="#00ff00"
ctx.lineWidth=3
ctx.strokeRect(x,y,w,h)

if(this.plate){

ctx.font="20px Arial"
ctx.fillStyle="#00ff00"
ctx.fillText(this.plate,x,y-10)

}

}

},

beforeUnmount(){

clearInterval(this.pollTimer)

}

}

</script>


<style scoped>

.security-container{
width:900px;
margin:auto;
text-align:center;
font-family:Arial;
}

.video-wrapper{
width:800px;
height:450px;
background:black;
margin:auto;
position:relative;
margin-top:20px;
}

.video{
width:100%;
height:100%;
object-fit:contain;

/* xoay lại camera */
transform: rotate(-90deg);
transform-origin:center;
}

.overlay{
position:absolute;
top:0;
left:0;
width:100%;
height:100%;
pointer-events:none;

/* xoay canvas giống video */
transform: rotate(-90deg);
transform-origin:center;
}
.video-off{
color:white;
display:flex;
justify-content:center;
align-items:center;
height:100%;
font-size:20px;
}

.plate-panel{
margin-top:20px;
}

.plate-number{
font-size:40px;
color:#00aa00;
font-weight:bold;
}

</style>