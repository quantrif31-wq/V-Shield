<template>
  <div>
    <h2>📷 Quản lý Camera</h2>

    <!-- FORM -->
    <input v-model="form.cameraName" placeholder="Tên camera" />
    <input v-model="form.gateId" placeholder="Gate ID" />
    <input v-model="form.cameraType" placeholder="Loại" />
    <input v-model="form.streamUrl" placeholder="RTSP URL" />

    <button @click="handleSubmit">
      {{ form.cameraId ? "Cập nhật" : "Thêm" }}
    </button>
    <button v-if="form.cameraId" @click="resetForm">Hủy</button>

    <br /><br />

    <!-- 🔥 BUTTON GO2RTC -->
    <button @click="reload">🚀 Reload Go2RTC</button>
    <button @click="stop">🛑 Stop Go2RTC</button>

    <br /><br />

    <!-- TABLE -->
    <table border="1">
      <thead>
        <tr>
          <th>ID</th>
          <th>Tên</th>
          <th>Gate</th>
          <th>Loại</th>
          <th>Stream</th>
          <th>View</th>
          <th>Hành động</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="cam in cameras" :key="cam.cameraId">
          <td>{{ cam.cameraId }}</td>
          <td>{{ cam.cameraName }}</td>
          <td>{{ cam.gateName }}</td>
          <td>{{ cam.cameraType }}</td>
          <td>{{ cam.streamUrl }}</td>

          <!-- 🔥 LINK XEM -->
          <td>
            <a v-if="cam.urlView" :href="cam.urlView" target="_blank">
              Xem
            </a>
            <span v-else>Chưa có</span>
          </td>

          <td>
            <button @click="edit(cam)">Sửa</button>
            <button @click="remove(cam.cameraId)">Xóa</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import {
  getCameras,
  createCamera,
  updateCamera,
  deleteCamera,
  reloadGo2rtc,
  stopGo2rtc,
} from "../services/setcamAPI";

export default {
  data() {
    return {
      cameras: [],
      form: {
        cameraId: null,
        cameraName: "",
        gateId: "",
        cameraType: "",
        streamUrl: "",
      },
    };
  },

  methods: {
    async loadData() {
      const res = await getCameras();
      this.cameras = res;
    },

    async handleSubmit() {
      const payload = {
        cameraName: this.form.cameraName,
        gateId: this.form.gateId ? Number(this.form.gateId) : null,
        cameraType: this.form.cameraType,
        streamUrl: this.form.streamUrl,
      };

      if (this.form.cameraId) {
        await updateCamera(this.form.cameraId, payload);
      } else {
        await createCamera(payload);
      }

      this.resetForm();
      await this.loadData();
    },

    edit(cam) {
      this.form = { ...cam };
    },

    async remove(id) {
      if (!confirm("Xóa camera này?")) return;
      await deleteCamera(id);
      await this.loadData();
    },

    async reload() {
      try {
        await reloadGo2rtc();
        alert("Reload thành công!");
        await this.loadData(); // load lại để thấy UrlView
      } catch (err) {
        alert("Lỗi reload!");
      }
    },

    async stop() {
      await stopGo2rtc();
      alert("Đã stop go2rtc");
    },

    resetForm() {
      this.form = {
        cameraId: null,
        cameraName: "",
        gateId: "",
        cameraType: "",
        streamUrl: "",
      };
    },
  },

  mounted() {
    this.loadData();
  },
};
</script>