<template>
  <div class="setcam-page">
    <h2>Quan ly Camera</h2>

    <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="message success">{{ successMessage }}</p>

    <div class="form-grid">
      <input v-model="form.cameraName" placeholder="Ten camera" />
      <input v-model="form.gateId" placeholder="Gate ID" />
      <input v-model="form.cameraType" placeholder="Loai camera" />
      <input v-model="form.streamUrl" placeholder="RTSP URL" />
    </div>

    <div class="actions">
      <button @click="handleSubmit">
        {{ form.cameraId ? "Cap nhat" : "Them" }}
      </button>
      <button v-if="form.cameraId" @click="resetForm">Huy</button>
      <button @click="reload">Reload Go2RTC</button>
      <button @click="stop">Stop Go2RTC</button>
    </div>

    <table border="1">
      <thead>
        <tr>
          <th>ID</th>
          <th>Ten</th>
          <th>Gate</th>
          <th>Loai</th>
          <th>Stream</th>
          <th>View</th>
          <th>Hanh dong</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="cam in cameras" :key="cam.cameraId">
          <td>{{ cam.cameraId }}</td>
          <td>{{ cam.cameraName }}</td>
          <td>{{ cam.gateName || "-----" }}</td>
          <td>{{ cam.cameraType || "-----" }}</td>
          <td>{{ cam.streamUrl || "-----" }}</td>
          <td>
            <a v-if="cam.urlView" :href="cam.urlView" target="_blank" rel="noreferrer">
              Xem
            </a>
            <span v-else>Chua co</span>
          </td>
          <td>
            <button @click="edit(cam)">Sua</button>
            <button @click="remove(cam.cameraId)">Xoa</button>
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
      errorMessage: "",
      successMessage: "",
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
      try {
        this.errorMessage = "";
        const res = await getCameras();
        this.cameras = res;
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.message ||
          "Khong tai duoc danh sach camera.";
      }
    },

    async handleSubmit() {
      this.errorMessage = "";
      this.successMessage = "";

      const cameraName = String(this.form.cameraName || "").trim();
      const cameraType = String(this.form.cameraType || "").trim();
      const streamUrl = String(this.form.streamUrl || "").trim();
      const rawGateId = String(this.form.gateId ?? "").trim();

      if (!cameraName) {
        this.errorMessage = "Ten camera khong duoc de trong.";
        return;
      }

      if (rawGateId && !/^\d+$/.test(rawGateId)) {
        this.errorMessage = "Gate ID phai la so nguyen hop le.";
        return;
      }

      const payload = {
        cameraName,
        gateId: rawGateId ? Number(rawGateId) : null,
        cameraType: cameraType || null,
        streamUrl: streamUrl || null,
      };

      try {
        if (this.form.cameraId) {
          await updateCamera(this.form.cameraId, payload);
          this.successMessage = "Cap nhat camera thanh cong.";
        } else {
          await createCamera(payload);
          this.successMessage = "Them camera thanh cong.";
        }

        this.resetForm();
        await this.loadData();
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.response?.data ||
          error?.message ||
          "Khong luu duoc camera.";
      }
    },

    edit(cam) {
      this.errorMessage = "";
      this.successMessage = "";
      this.form = {
        cameraId: cam.cameraId ?? null,
        cameraName: cam.cameraName ?? "",
        gateId: cam.gateId ?? "",
        cameraType: cam.cameraType ?? "",
        streamUrl: cam.streamUrl ?? "",
      };
    },

    async remove(id) {
      if (!confirm("Xoa camera nay?")) return;

      this.errorMessage = "";
      this.successMessage = "";

      try {
        await deleteCamera(id);
        this.successMessage = "Xoa camera thanh cong.";
        await this.loadData();
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.response?.data ||
          error?.message ||
          "Khong xoa duoc camera.";
      }
    },

    async reload() {
      this.errorMessage = "";
      this.successMessage = "";

      try {
        await reloadGo2rtc();
        this.successMessage = "Reload Go2RTC thanh cong.";
        await this.loadData();
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.message ||
          "Loi reload Go2RTC.";
      }
    },

    async stop() {
      this.errorMessage = "";
      this.successMessage = "";

      try {
        await stopGo2rtc();
        this.successMessage = "Da stop go2rtc.";
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.message ||
          "Khong tat duoc go2rtc.";
      }
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

<style scoped>
.setcam-page {
  display: grid;
  gap: 12px;
}

.form-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.message {
  margin: 0;
  padding: 10px 12px;
  border-radius: 10px;
}

.message.error {
  background: #feeceb;
  color: #b42318;
}

.message.success {
  background: #e8fff1;
  color: #067647;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 8px;
  text-align: left;
}
</style>
