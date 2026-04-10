<template>
  <div class="page-container ops-page animate-in">
    <!-- Page Header -->
    <div class="page-header-bar">
      <div>
        <span class="panel-kicker">Camera Management</span>
        <h1 class="page-title">Quản trị Camera</h1>
        <p class="page-subtitle">Quản lý danh sách camera, cấu hình stream và tích hợp Go2RTC.</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="reload">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          Reload Go2RTC
        </button>
        <button class="btn btn-danger-outline" @click="stop">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>
          Dừng Go2RTC
        </button>
      </div>
    </div>

    <!-- Toast Messages -->
    <transition name="toast">
      <div v-if="errorMessage" class="toast-message toast-error" @click="errorMessage = ''">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
        <span>{{ errorMessage }}</span>
      </div>
    </transition>
    <transition name="toast">
      <div v-if="successMessage" class="toast-message toast-success" @click="successMessage = ''">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        <span>{{ successMessage }}</span>
      </div>
    </transition>

    <!-- Camera Form Card -->
    <section class="cam-form-card">
      <div class="cam-form-header">
        <div class="cam-form-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
        </div>
        <div>
          <h2 class="cam-form-title">{{ form.cameraId ? 'Cập nhật camera' : 'Thêm camera mới' }}</h2>
          <p class="cam-form-desc">{{ form.cameraId ? 'Chỉnh sửa thông tin camera đang chọn' : 'Điền thông tin camera mới để thêm vào hệ thống' }}</p>
        </div>
      </div>

      <div class="cam-form-grid">
        <div class="form-group">
          <label>Tên camera <span class="required">*</span></label>
          <input v-model="form.cameraName" placeholder="VD: Camera cổng chính" />
        </div>
        <div class="form-group">
          <label>Gate ID</label>
          <input v-model="form.gateId" placeholder="VD: 1" />
        </div>
        <div class="form-group">
          <label>Loại camera</label>
          <input v-model="form.cameraType" placeholder="VD: LPR, QR, FaceID..." />
        </div>
        <div class="form-group">
          <label>RTSP URL</label>
          <input v-model="form.streamUrl" placeholder="rtsp://..." class="mono-input" />
        </div>
      </div>

      <div class="cam-form-actions">
        <button class="btn btn-primary" @click="handleSubmit">
          <svg v-if="!form.cameraId" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          {{ form.cameraId ? 'Cập nhật' : 'Thêm camera' }}
        </button>
        <button v-if="form.cameraId" class="btn btn-secondary" @click="resetForm">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          Huỷ
        </button>
      </div>
    </section>

    <!-- Camera List -->
    <section class="cam-list-section">
      <div class="cam-list-header">
        <div>
          <span class="panel-kicker">Danh sách</span>
          <h2 class="section-title">Camera đã đăng ký</h2>
        </div>
        <span class="cam-count-badge">{{ cameras.length }} camera</span>
      </div>

      <div v-if="cameras.length" class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Tên camera</th>
              <th>Gate</th>
              <th>Loại</th>
              <th>Stream URL</th>
              <th>Xem trực tiếp</th>
              <th style="text-align: right;">Hành động</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cam in cameras" :key="cam.cameraId">
              <td>
                <span class="cam-id-pill">#{{ cam.cameraId }}</span>
              </td>
              <td>
                <div class="cam-name-cell">
                  <div class="cam-name-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                  </div>
                  <strong>{{ cam.cameraName }}</strong>
                </div>
              </td>
              <td>
                <span v-if="cam.gateName" class="badge info">{{ cam.gateName }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td>
                <span v-if="cam.cameraType" class="badge-type">{{ cam.cameraType }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td>
                <span v-if="cam.streamUrl" class="stream-url" :title="cam.streamUrl">{{ truncateUrl(cam.streamUrl) }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td>
                <a v-if="cam.urlView" :href="cam.urlView" target="_blank" rel="noreferrer" class="view-link">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  Xem trực tiếp
                </a>
                <span v-else class="text-muted">Chưa có</span>
              </td>
              <td>
                <div class="action-cell">
                  <button class="btn-action btn-edit" @click="edit(cam)" title="Sửa camera">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                  </button>
                  <button class="btn-action btn-delete" @click="remove(cam.cameraId)" title="Xoá camera">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
        </div>
        <h3>Chưa có camera nào</h3>
        <p>Thêm camera đầu tiên bằng form phía trên để bắt đầu.</p>
      </div>
    </section>
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
    truncateUrl(url, max = 40) {
      if (!url) return "";
      return url.length > max ? url.slice(0, max) + "..." : url;
    },

    async loadData() {
      try {
        this.errorMessage = "";
        const res = await getCameras();
        this.cameras = res;
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.message ||
          "Không tải được danh sách camera.";
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
        this.errorMessage = "Tên camera không được để trống.";
        return;
      }

      if (rawGateId && !/^\d+$/.test(rawGateId)) {
        this.errorMessage = "Gate ID phải là số nguyên hợp lệ.";
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
          this.successMessage = "Cập nhật camera thành công.";
        } else {
          await createCamera(payload);
          this.successMessage = "Thêm camera thành công.";
        }

        this.resetForm();
        await this.loadData();
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.response?.data ||
          error?.message ||
          "Không lưu được camera.";
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

      // Scroll to form
      window.scrollTo({ top: 0, behavior: "smooth" });
    },

    async remove(id) {
      if (!confirm("Bạn có chắc muốn xoá camera này?")) return;

      this.errorMessage = "";
      this.successMessage = "";

      try {
        await deleteCamera(id);
        this.successMessage = "Xoá camera thành công.";
        await this.loadData();
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.response?.data ||
          error?.message ||
          "Không xoá được camera.";
      }
    },

    async reload() {
      this.errorMessage = "";
      this.successMessage = "";

      try {
        await reloadGo2rtc();
        this.successMessage = "Reload Go2RTC thành công.";
        await this.loadData();
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.message ||
          "Lỗi reload Go2RTC.";
      }
    },

    async stop() {
      this.errorMessage = "";
      this.successMessage = "";

      try {
        await stopGo2rtc();
        this.successMessage = "Đã dừng Go2RTC.";
      } catch (error) {
        this.errorMessage =
          error?.response?.data?.message ||
          error?.message ||
          "Không tắt được Go2RTC.";
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
/* ========== Page Header ========== */
.page-header-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-danger-outline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.98rem;
  white-space: nowrap;
  background: rgba(195, 81, 70, 0.08);
  border: 1px solid rgba(195, 81, 70, 0.22);
  color: var(--accent-danger);
  transition: all var(--transition-fast);
}

.btn-danger-outline:hover {
  background: rgba(195, 81, 70, 0.14);
  border-color: rgba(195, 81, 70, 0.38);
  transform: translateY(-1px);
}

/* ========== Toast Messages ========== */
.toast-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-radius: var(--border-radius-sm);
  margin-bottom: 18px;
  font-weight: 600;
  font-size: 0.94rem;
  cursor: pointer;
  animation: slideDown 0.32s ease;
  backdrop-filter: blur(12px);
}

.toast-error {
  background: rgba(195, 81, 70, 0.1);
  border: 1px solid rgba(195, 81, 70, 0.22);
  color: var(--accent-danger);
}

.toast-success {
  background: rgba(20, 134, 109, 0.1);
  border: 1px solid rgba(20, 134, 109, 0.22);
  color: var(--accent-success);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ========== Camera Form Card ========== */
.cam-form-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-sm);
  backdrop-filter: var(--glass-blur);
  padding: 28px;
  margin-bottom: 28px;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.cam-form-card:hover {
  border-color: var(--border-color-hover);
  box-shadow: var(--shadow-md);
}

.cam-form-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.cam-form-icon {
  width: 50px;
  height: 50px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(15, 124, 130, 0.12);
  color: var(--accent-primary);
}

.cam-form-title {
  font-family: var(--font-heading);
  font-size: 1.24rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.cam-form-desc {
  font-size: 0.9rem;
  color: var(--text-muted);
}

.cam-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.cam-form-grid .form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 0.88rem;
  font-weight: 600;
}

.required {
  color: var(--accent-danger);
}

.cam-form-grid .form-group input {
  width: 100%;
  min-height: 46px;
  padding: 0 16px;
  border-radius: 14px;
  border: 1px solid rgba(24, 49, 77, 0.1);
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 0.98rem;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
}

.cam-form-grid .form-group input:focus {
  border-color: rgba(15, 124, 130, 0.36);
  box-shadow: 0 0 0 4px rgba(84, 196, 211, 0.18);
  background: rgba(255, 255, 255, 0.96);
}

.cam-form-grid .form-group input::placeholder {
  color: var(--text-muted);
}

.mono-input {
  font-family: 'IBM Plex Mono', 'Consolas', monospace !important;
  font-size: 0.9rem !important;
  letter-spacing: -0.02em;
}

.cam-form-actions {
  display: flex;
  gap: 10px;
}

/* ========== Camera List ========== */
.cam-list-section {
  margin-bottom: 28px;
}

.cam-list-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
}

.section-title {
  font-family: var(--font-heading);
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 4px;
}

.cam-count-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 0.86rem;
  font-weight: 700;
  background: rgba(15, 124, 130, 0.1);
  color: var(--accent-primary);
  white-space: nowrap;
}

/* ========== Table ========== */
.table-container {
  overflow-x: auto;
  border-radius: var(--border-radius);
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
  backdrop-filter: var(--glass-blur);
}

.cam-id-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(43, 109, 138, 0.1);
  color: var(--accent-secondary);
  font-family: 'IBM Plex Mono', monospace;
}

.cam-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cam-name-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(84, 196, 211, 0.12);
  color: var(--accent-info);
  flex-shrink: 0;
}

.cam-name-cell strong {
  font-size: 0.94rem;
}

.badge-type {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(216, 155, 55, 0.12);
  color: var(--accent-warning);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stream-url {
  font-family: 'IBM Plex Mono', 'Consolas', monospace;
  font-size: 0.82rem;
  color: var(--text-muted);
  letter-spacing: -0.02em;
}

.view-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 0.84rem;
  font-weight: 700;
  background: rgba(20, 134, 109, 0.1);
  color: var(--accent-success);
  transition: all var(--transition-fast);
  text-decoration: none;
}

.view-link:hover {
  background: rgba(20, 134, 109, 0.18);
  transform: translateY(-1px);
}

.text-muted {
  color: var(--text-muted);
  font-size: 0.88rem;
}

/* ========== Action Buttons ========== */
.action-cell {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn-action {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.76);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.btn-edit:hover {
  color: var(--accent-primary);
  border-color: var(--border-color-hover);
  background: rgba(15, 124, 130, 0.08);
  transform: translateY(-1px);
}

.btn-delete:hover {
  color: var(--accent-danger);
  border-color: rgba(195, 81, 70, 0.28);
  background: rgba(195, 81, 70, 0.08);
  transform: translateY(-1px);
}

/* ========== Empty State ========== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 28px;
  border-radius: var(--border-radius);
  border: 2px dashed var(--border-color);
  background: rgba(255, 255, 255, 0.54);
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(84, 196, 211, 0.1);
  color: var(--accent-info);
  margin-bottom: 18px;
}

.empty-state h3 {
  font-family: var(--font-heading);
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-muted);
  font-size: 0.94rem;
  max-width: 38ch;
}

/* ========== Responsive ========== */
@media (max-width: 768px) {
  .page-header-bar {
    flex-direction: column;
    gap: 14px;
  }

  .cam-form-grid {
    grid-template-columns: 1fr;
  }

  .cam-form-actions {
    flex-direction: column;
  }

  .cam-form-actions .btn {
    width: 100%;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .btn,
  .header-actions .btn-danger-outline {
    flex: 1;
    min-width: 0;
  }
}
</style>
