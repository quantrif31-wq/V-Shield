<template>

<div class="security-container">

  <h1 class="title">Gate Camera Monitor</h1>

  <!-- CAMERA -->
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

  <!-- PLATE -->
  <div class="plate-panel">

    <div class="plate-label">Detected Plate</div>

    <div class="plate-number">
      {{ plate || "-----" }}
    </div>

    <div class="fps">
      FPS: {{ fps }}
    </div>

  </div>

  <!-- CONTROLS -->
  <div class="controls">

  <input
    v-model="cameraIp"
    placeholder="Camera MJPEG URL"
    class="ip-input"
  />

  <button
    class="btn ai-on"
    @click="startAI"
  >
    Start AI
  </button>

  <button
    class="btn ai-off"
    @click="stopAI"
  >
    Stop AI
  </button>

  <button
    class="btn start"
    @click="startCameraClick"
  >
    Start Camera
  </button>

  <button
    class="btn stop"
    @click="stopCameraClick"
  >
    Stop Camera
  </button>

</div>

</div>

</template>


<script>

import { startCamera, 
  stopCamera,
  getPlate,
  getStatus,
  shutdownAI} from "../services/biensoApi"

export default {

  name: "SecurityPlateMonitor",

  data() {
    return {

      cameraIp: "",
      plate: "",
      fps: 0,

      cameraRunning: false,

      streamUrl: "",

      pollTimer: null

    }
  },

  methods: {

    async startCameraClick() {

      if (!this.cameraIp) {

        alert("Enter camera URL")
        return

      }

      try {

        const res = await startCamera(this.cameraIp)

        console.log("Camera started:", res)

        this.cameraRunning = true

        // open camera stream directly
        this.streamUrl = this.cameraIp

        this.startPolling()

      }
      catch (err) {

        console.error(err)

        alert("Cannot start camera")

      }

    },
async startAI() {

  try {

    const res = await getStatus()

    console.log("AI Started:", res)

    alert("AI Server Started")

  }
  catch (err) {

    console.error(err)

    alert("Cannot start AI")

  }

},

async stopAI() {

  try {

    const res = await shutdownAI()

    console.log("AI stopped:", res)

    this.cameraRunning = false
    this.plate = ""

    clearInterval(this.pollTimer)

    alert("AI Server Stopped")

  }
  catch (err) {

    console.error(err)

    alert("Cannot stop AI")

  }

},

    async stopCameraClick() {

      this.cameraRunning = false

      this.plate = ""

      clearInterval(this.pollTimer)

      const canvas = this.$refs.canvas
      const ctx = canvas.getContext("2d")

      ctx.clearRect(0,0,canvas.width,canvas.height)

    },


    startPolling() {

      if (this.pollTimer)
        clearInterval(this.pollTimer)

      this.pollTimer = setInterval(async () => {

        try {

          const res = await getPlate()

          if (!res) return

          if (res.plate)
            this.plate = res.plate

          this.fps = res.fps

          this.drawBox(res.box)

        }
        catch (err) {

          console.log("Polling error")

        }

      }, 700)

    },


    drawBox(box) {

      const canvas = this.$refs.canvas
      const ctx = canvas.getContext("2d")

      const img = this.$refs.video

      if (!img) return

      canvas.width = img.clientWidth
      canvas.height = img.clientHeight

      ctx.clearRect(0,0,canvas.width,canvas.height)

      if (!box) return

      const scaleX = canvas.width / 640
      const scaleY = canvas.height / 360

      const x = box.x1 * scaleX
      const y = box.y1 * scaleY
      const w = (box.x2 - box.x1) * scaleX
      const h = (box.y2 - box.y1) * scaleY

      ctx.strokeStyle = "#00ff00"
      ctx.lineWidth = 3

      ctx.strokeRect(x,y,w,h)

      ctx.font = "20px Arial"
      ctx.fillStyle = "#00ff00"

      if (this.plate)
        ctx.fillText(this.plate, x, y - 10)

    }

  },

  beforeUnmount() {

    clearInterval(this.pollTimer)

  }

}

</script>



<style scoped>

.security-container{
width:900px;
margin:auto;
font-family:Arial;
text-align:center;
}

.title{
margin-bottom:20px;
}


.video-wrapper{
width:800px;
height:450px;
margin:auto;
background:#000;
border-radius:6px;
overflow:hidden;
position:relative;
}


.video{
width:100%;
height:100%;
object-fit:cover;
}


.overlay{
position:absolute;
left:0;
top:0;
width:100%;
height:100%;
pointer-events:none;
}


.video-off{
color:white;
display:flex;
align-items:center;
justify-content:center;
height:100%;
font-size:20px;
}


.plate-panel{
margin-top:20px;
}

.plate-label{
font-size:18px;
color:#666;
}

.plate-number{
font-size:42px;
font-weight:bold;
color:#00aa00;
margin-top:5px;
letter-spacing:3px;
}

.fps{
color:#888;
margin-top:5px;
}


.controls{
margin-top:25px;
}

.ip-input{
width:320px;
padding:8px;
margin-right:10px;
border:1px solid #ccc;
border-radius:4px;
}

.btn{
padding:10px 20px;
margin:5px;
cursor:pointer;
border:none;
color:white;
border-radius:4px;
}

.start{
background:#28a745;
}

.stop{
background:#dc3545;
}
.ai-on{
background:#007bff;
}

.ai-off{
background:#6c757d;
}
</style>