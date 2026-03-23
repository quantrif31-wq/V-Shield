<script setup>
import { reactive } from "vue"

const brokenImages = reactive({})

const logo = {
  src: "/images/team/logo.jpg",
  alt: "V-Shield Logo",
  scale: 1.35,
  position: "center center",
}

const advisor = {
  name: "ThS. Phan Hoàng Khải",
  role: "Giáo viên hướng dẫn",
  image: "/images/team/thaykhai.jpg",
  imagePosition: "center 16%",
  badgeClass: "",
  badgeStyle: {
    background: "rgba(245, 158, 11, 0.15)",
    color: "var(--accent-warning)",
  },
}

const featureCards = [
  {
    title: "Virtual Checkpoint (Thanh chắn ảo)",
    tone: "green",
    description:
      "Loại bỏ rào cản vật lý, sử dụng hệ thống đèn tín hiệu ảo (xanh, vàng, đỏ) trên dashboard để điều phối giao thông mượt mà.",
  },
  {
    title: "Draft Area (Vùng đệm xử lý)",
    tone: "orange",
    description:
      "Trao quyền kiểm soát linh hoạt cho bảo vệ xử lý các tình huống ngoại lệ ngay trên màn hình theo thời gian thực mà không làm sập luồng dữ liệu.",
  },
  {
    title: "Audit Trail (Lưu vết vĩnh viễn)",
    tone: "blue",
    description:
      "Áp dụng ràng buộc khóa chéo XOR và ghép cặp IN-OUT khép kín. Mọi thao tác cấp phép cưỡng chế đều phải gắn mã lý do và bị lưu vết vĩnh viễn.",
  },
]

const teamMembers = [
  {
    name: "Phạm Văn Thành",
    role: "Dev chính",
    image: "/images/team/thanh.jpg",
    imagePosition: "center 16%",
    badgeClass: "active",
  },
  {
    name: "Hà Mạnh Hùng",
    role: "Back-end API",
    image: "/images/team/hung.jpg",
    imagePosition: "center 14%",
    badgeClass: "pending",
  },
  {
    name: "Phạm Ngọc Hoài Anh",
    role: "Leader / Back-end",
    image: "/images/team/anh.jpg",
    imagePosition: "center 15%",
    badgeClass: "info",
  },
  {
    name: "Vũ Tiến Đạt",
    role: "Front-end",
    image: "/images/team/dat.jpg",
    imagePosition: "center 15%",
    badgeClass: "",
    badgeStyle: {
      background: "rgba(139, 92, 246, 0.15)",
      color: "var(--accent-secondary)",
    },
  },
  {
    name: "Nguyễn Quốc Việt",
    role: "Database",
    image: "/images/team/viet.jpg",
    imagePosition: "center 14%",
    badgeClass: "",
    badgeStyle: {
      background: "rgba(239, 68, 68, 0.15)",
      color: "var(--accent-danger)",
    },
  },
]

const roadmapItems = [
  {
    title: "Tích hợp Edge AI",
    description:
      "Đưa thuật toán xử lý hình ảnh trực tiếp xuống các thiết bị camera tại biên để giảm tải cho server trung tâm.",
  },
  {
    title: "Mở rộng Pre-registration",
    description:
      "Triển khai luồng gửi SMS hoặc email tự động chứa mã QR cho khách vãng lai tự khai báo thông tin trước khi đến.",
  },
  {
    title: "Data Analytics & Multi-tenant",
    description:
      "Phát triển module thống kê biểu đồ nhiệt về lưu lượng ra vào và nâng cấp kiến trúc hệ thống để phục vụ mô hình nhiều công ty.",
  },
]

const getPortraitStyle = (position = "center 20%") => ({
  objectPosition: position,
})

const getLogoStyle = () => ({
  transform: `scale(${logo.scale})`,
  transformOrigin: logo.position,
})

const markImageBroken = (path) => {
  if (path) {
    brokenImages[path] = true
  }
}

const canShowImage = (path) => Boolean(path) && !brokenImages[path]

const getInitials = (name) =>
  (name || "")
    .split(" ")
    .filter(Boolean)
    .slice(-2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("") || "VS"
</script>

<template>
  <div class="page-container animate-in">
    <div class="profile-header">
      <div class="logo-wrapper">
        <img
          v-if="canShowImage(logo.src)"
          :src="logo.src"
          :alt="logo.alt"
          class="logo-img"
          :style="getLogoStyle()"
          @error="markImageBroken(logo.src)"
        />
        <div v-else class="logo-fallback">VS</div>
      </div>

      <div class="header-text">
        <h1 class="page-title">V-SHIELD | SMART ACCESS CONTROL</h1>
        <p class="page-subtitle">
          V-Shield là hệ thống kiểm soát an ninh ra vào thông minh được thiết kế
          theo chuẩn enterprise. Bằng việc số hóa 100% quy trình đối chiếu tại
          cổng gác, hệ thống loại bỏ hoàn toàn sổ sách thủ công, giải quyết
          triệt để điểm nghẽn giao thông và mang lại nguồn dữ liệu định danh
          minh bạch cho doanh nghiệp.
        </p>
      </div>
    </div>

    <div class="bento-grid profile-grid">
      <div class="bento-card col-span-4 project-intro">
        <h2 class="section-title">Giới thiệu dự án (The Project)</h2>

        <div class="core-description">
          <strong>Mô tả cốt lõi:</strong> V-Shield vận hành dựa trên kiến trúc
          phân tách độc lập giữa Vue.js Frontend và ASP.NET Core Web API. Hệ
          thống tiếp nhận luồng dữ liệu thời gian thực từ camera AI, bóc tách
          biển số xe và khuôn mặt người điều khiển để đối chiếu với cơ sở dữ
          liệu nội bộ trong thời gian cực ngắn.
        </div>

        <div class="three-col-grid">
          <div
            v-for="feature in featureCards"
            :key="feature.title"
            class="feature-card"
          >
            <div class="feature-icon">
              <span class="pulse-dot" :class="feature.tone"></span>
            </div>
            <h4>{{ feature.title }}</h4>
            <p>{{ feature.description }}</p>
          </div>
        </div>
      </div>

      <div class="bento-card col-span-4 team-card">
        <div class="card-header card-header-center">
          <h2 class="section-title section-title-no-margin">
            Đội ngũ phát triển dự án
          </h2>
        </div>

        <div class="advisor-row">
          <div class="team-member advisor-card">
            <div class="member-avatar advisor-avatar">
              <img
                v-if="canShowImage(advisor.image)"
                :src="advisor.image"
                :alt="advisor.role"
                :style="getPortraitStyle(advisor.imagePosition)"
                @error="markImageBroken(advisor.image)"
              />
              <div v-else class="avatar-fallback">
                {{ getInitials(advisor.name) }}
              </div>
            </div>
            <h4 class="member-name">{{ advisor.name }}</h4>
            <span
              class="badge"
              :class="advisor.badgeClass"
              :style="advisor.badgeStyle"
            >
              {{ advisor.role }}
            </span>
          </div>
        </div>

        <div class="team-row">
          <div
            v-for="member in teamMembers"
            :key="member.name"
            class="team-member"
            :class="{ 'leader-card': member.role.includes('Leader') }"
          >
            <div class="member-avatar">
              <img
                v-if="canShowImage(member.image)"
                :src="member.image"
                :alt="member.name"
                :style="getPortraitStyle(member.imagePosition)"
                @error="markImageBroken(member.image)"
              />
              <div v-else class="avatar-fallback">
                {{ getInitials(member.name) }}
              </div>
            </div>
            <h4 class="member-name">{{ member.name }}</h4>
            <span
              class="badge"
              :class="member.badgeClass"
              :style="member.badgeStyle"
            >
              {{ member.role }}
            </span>
          </div>
        </div>
      </div>

      <div class="bento-card col-span-4 roadmap-section">
        <h2 class="section-title">Hướng đi tương lai (Future Roadmap)</h2>

        <div class="three-col-grid">
          <div
            v-for="item in roadmapItems"
            :key="item.title"
            class="feature-card roadmap"
          >
            <h4>{{ item.title }}</h4>
            <p>{{ item.description }}</p>
          </div>
        </div>
      </div>

      <router-link
        to="/dashboard"
        class="bento-card col-span-4 interactive-card action-primary cta-card"
      >
        <div>
          <h3 class="cta-title">Hệ thống đã sẵn sàng</h3>
          <p class="cta-subtitle">
            Trải nghiệm quá trình kiểm soát an ninh tự động hóa.
          </p>
          <button class="btn btn-secondary cta-button">
            Truy cập Dashboard →
          </button>
        </div>
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.profile-grid {
  grid-auto-rows: minmax(min-content, auto);
  gap: 24px;
}

.col-span-4 {
  grid-column: span 4;
}

.section-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 24px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.section-title-no-margin {
  margin: 0;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 32px;
  margin-bottom: 40px;
  background: linear-gradient(145deg, var(--bg-card), var(--bg-primary));
  padding: 32px;
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
}

.logo-wrapper {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  border: 3px solid var(--accent-primary);
  box-shadow: 0 0 25px rgba(16, 121, 196, 0.35);
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.logo-fallback,
.avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--accent-primary);
  background: linear-gradient(145deg, rgba(16, 121, 196, 0.12), rgba(16, 121, 196, 0.04));
}

.logo-fallback {
  font-size: 2rem;
}

.avatar-fallback {
  font-size: 1.5rem;
}

.header-text {
  flex: 1;
}

.header-text .page-title {
  font-size: 2rem;
  margin-bottom: 12px;
}

.header-text .page-subtitle {
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--text-secondary);
  max-width: 900px;
}

.three-col-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card {
  background: var(--bg-secondary);
  padding: 24px;
  border-radius: var(--border-radius-sm);
  border: 1px solid var(--border-color);
  transition: all var(--transition-normal);
}

.feature-card:hover {
  transform: translateY(-3px);
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-md);
}

.feature-card h4 {
  font-size: 1.1rem;
  color: var(--text-primary);
  margin-bottom: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.feature-card p {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.roadmap {
  border-left: 4px solid var(--accent-primary);
}

.core-description {
  background: rgba(16, 121, 196, 0.05);
  border-left: 4px solid var(--accent-primary);
  padding: 20px 24px;
  margin-bottom: 28px;
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--text-primary);
  border-radius: 0 var(--border-radius-sm) var(--border-radius-sm) 0;
}

.core-description strong {
  color: var(--accent-primary);
}

.feature-icon .pulse-dot {
  width: 12px;
  height: 12px;
  display: inline-block;
  border-radius: 50%;
  box-shadow: 0 0 10px currentColor;
}

.green {
  color: var(--accent-success);
  background: var(--accent-success);
}

.orange {
  color: var(--accent-warning);
  background: var(--accent-warning);
}

.blue {
  color: var(--accent-primary);
  background: var(--accent-primary);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header-center {
  justify-content: center;
  margin-bottom: 32px;
}

.advisor-row {
  display: flex;
  justify-content: center;
  margin-bottom: 40px;
  position: relative;
}

.advisor-row::after {
  content: "";
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
}

.team-row {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
  padding: 20px 0;
}

.team-member {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  flex: 1;
  min-width: 140px;
  transition: transform var(--transition-normal);
}

.team-member:hover {
  transform: translateY(-5px);
}

.member-avatar {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  margin-bottom: 16px;
  background: var(--bg-secondary);
  border: 3px solid var(--border-color);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: border-color var(--transition-fast);
}

.team-member:hover .member-avatar {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow);
}

.member-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.advisor-avatar {
  width: 140px;
  height: 140px;
  border-color: var(--accent-warning);
  box-shadow: 0 0 15px rgba(245, 158, 11, 0.2);
}

.member-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.cta-card {
  text-align: center;
  padding: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.interactive-card {
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  transition: all var(--transition-normal);
}

.interactive-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-color-hover);
}

.action-primary {
  background: linear-gradient(145deg, var(--bg-card), var(--bg-card-hover));
}

.cta-title {
  font-size: 1.4rem;
  margin-bottom: 8px;
}

.cta-subtitle {
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.cta-button {
  font-size: 1rem;
  padding: 12px 24px;
}

@media (max-width: 1024px) {
  .profile-header {
    flex-direction: column;
    text-align: center;
  }

  .three-col-grid {
    grid-template-columns: 1fr;
  }

  .team-row {
    gap: 20px;
  }

  .leader-card {
    transform: scale(1);
    margin: 0;
  }
}

@media (max-width: 768px) {
  .col-span-4 {
    grid-column: span 1 !important;
  }

  .profile-header {
    padding: 20px;
    gap: 16px;
  }

  .logo-wrapper {
    width: 100px;
    height: 100px;
  }

  .header-text .page-title {
    font-size: 1.5rem;
  }

  .header-text .page-subtitle {
    font-size: 0.95rem;
  }

  .feature-card,
  .core-description,
  .cta-card {
    padding: 16px;
  }

  .team-row {
    gap: 16px;
  }

  .team-member {
    min-width: 45%;
  }

  .member-avatar {
    width: 88px;
    height: 88px;
  }
}
</style>
