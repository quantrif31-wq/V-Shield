<template>
  <div class="page">
    <div class="card">
      <h2>Tạo QR động nhân viên</h2>

      <div class="form-group">
        <label for="employeeId">Employee ID</label>
        <input
          id="employeeId"
          v-model="employeeId"
          type="number"
          min="1"
          placeholder="Nhập Employee ID"
          @keyup.enter="startGenerate"
        />
      </div>

      <div class="actions">
        <button @click="startGenerate" :disabled="loading">
          {{ loading ? "Đang tạo..." : "Tạo QR động" }}
        </button>

        <button class="secondary" @click="stopAutoRefresh">
          Dừng realtime
        </button>
      </div>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success">{{ successMessage }}</p>
    </div>

    <div v-if="qrData" class="card qr-card">
      <h3>Thông tin QR động</h3>

      <div class="info-grid">
        <div><strong>Employee ID:</strong> {{ qrData.employeeId }}</div>
        <div><strong>Họ tên:</strong> {{ qrData.employeeName }}</div>
        <div><strong>OTP:</strong> {{ qrData.otp }}</div>
        <div><strong>Chu kỳ:</strong> {{ qrData.timeStepSeconds }} giây</div>
        <div><strong>Generated UTC:</strong> {{ formatDate(qrData.generatedAtUtc) }}</div>
        <div><strong>Expires UTC:</strong> {{ formatDate(qrData.expiresAtUtc) }}</div>
      </div>

      <div class="countdown-wrap">
        <div class="countdown-label">Còn lại</div>
        <div class="countdown-value">{{ remainingSeconds }}s</div>
      </div>

      <div class="qr-box">
        <img v-if="qrImage" :src="qrImage" alt="Dynamic QR" />
      </div>

      <div class="payload-box">
        <label>QR Payload</label>
        <textarea rows="4" readonly :value="qrData.qrPayload"></textarea>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from "vue";
import QRCode from "qrcode";
import { generateDynamicQr } from "../services/dynamicQrApi";

const employeeId = ref("");
const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const qrData = ref(null);
const qrImage = ref("");
const remainingSeconds = ref(0);

let intervalId = null;
let currentEmployeeId = null;

function clearMessages() {
  errorMessage.value = "";
  successMessage.value = "";
}

function stopAutoRefresh() {
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = null;
  }
}

async function renderQr(payload) {
  qrImage.value = await QRCode.toDataURL(payload, {
    width: 280,
    margin: 2,
  });
}

async function fetchQr(employeeIdValue) {
  loading.value = true;
  clearMessages();

  try {
    const result = await generateDynamicQr(employeeIdValue);

    if (!result.success) {
      throw new Error(result.message || "Tạo QR thất bại.");
    }

    qrData.value = result.data;
    remainingSeconds.value = result.data.remainingSeconds ?? 0;
    await renderQr(result.data.qrPayload);

    successMessage.value = result.message || "Tạo QR thành công.";
  } catch (error) {
    errorMessage.value =
      error?.response?.data?.message ||
      error?.message ||
      "Không thể tạo QR động.";
  } finally {
    loading.value = false;
  }
}

async function startGenerate() {
  if (!employeeId.value) {
    errorMessage.value = "Vui lòng nhập Employee ID.";
    return;
  }

  currentEmployeeId = Number(employeeId.value);

  stopAutoRefresh();
  await fetchQr(currentEmployeeId);

  intervalId = setInterval(async () => {
    if (remainingSeconds.value > 1) {
      remainingSeconds.value -= 1;
      return;
    }

    if (currentEmployeeId) {
      await fetchQr(currentEmployeeId);
    }
  }, 1000);
}

function formatDate(dateValue) {
  if (!dateValue) return "";
  return new Date(dateValue).toLocaleString();
}

onBeforeUnmount(() => {
  stopAutoRefresh();
});
</script>

<style scoped>
.page {
  max-width: 900px;
  margin: 24px auto;
  padding: 16px;
}

.card {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 14px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
}

h2, h3 {
  margin-top: 0;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
}

input,
textarea {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #ccc;
  font-size: 14px;
  box-sizing: border-box;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

button {
  border: none;
  background: #2563eb;
  color: #fff;
  padding: 12px 18px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}

button.secondary {
  background: #6b7280;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #dc2626;
  margin-top: 12px;
  font-weight: 600;
}

.success {
  color: #16a34a;
  margin-top: 12px;
  font-weight: 600;
}

.qr-card {
  text-align: center;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  text-align: left;
  gap: 10px;
  margin-bottom: 20px;
}

.countdown-wrap {
  margin: 20px 0;
}

.countdown-label {
  color: #555;
  margin-bottom: 8px;
}

.countdown-value {
  font-size: 32px;
  font-weight: 700;
  color: #dc2626;
}

.qr-box {
  margin: 20px 0;
}

.qr-box img {
  max-width: 280px;
  width: 100%;
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.payload-box {
  text-align: left;
}
</style>