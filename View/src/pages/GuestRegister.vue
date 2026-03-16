<template>
    <div class="guest-register">
        <!-- Background decoration -->
        <div class="bg-decoration">
            <div class="bg-circle c1"></div>
            <div class="bg-circle c2"></div>
            <div class="bg-circle c3"></div>
        </div>

        <div class="register-container">
            <!-- Logo -->
            <div class="register-logo">
                <div class="logo-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L3 7V17L12 22L21 17V7L12 2Z" stroke="currentColor" stroke-width="2"
                            stroke-linejoin="round" />
                        <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" fill="currentColor" opacity="0.3" />
                        <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" stroke="currentColor" stroke-width="1.5"
                            stroke-linejoin="round" />
                    </svg>
                </div>
                <span class="logo-text">V-Shield</span>
            </div>

            <!-- ERROR STATE -->
            <div v-if="errorState" class="register-card error-card animate-in">
                <div class="state-icon error">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M15 9l-6 6" />
                        <path d="M9 9l6 6" />
                    </svg>
                </div>
                <h2>Không thể truy cập</h2>
                <p class="state-msg">{{ errorMessage }}</p>
                <a href="/" class="btn btn-secondary" style="margin-top: 16px;">Về trang chủ</a>
            </div>

            <!-- LOADING STATE -->
            <div v-else-if="isValidating" class="register-card animate-in">
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>Đang xác thực link đăng ký...</p>
                </div>
            </div>

            <!-- SUCCESS STATE -->
            <div v-else-if="isSubmitted" class="register-card success-card animate-in">
                <div class="state-icon success">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M9 12l2 2 4-4" />
                    </svg>
                </div>
                <h2>Đăng ký thành công!</h2>
                <p class="state-msg">Đơn đăng ký của bạn đã được gửi. Vui lòng chờ xác nhận từ nhân viên phụ trách.</p>
                <div class="success-details">
                    <div class="success-item">
                        <span class="s-label">Mã đơn</span>
                        <span class="s-value">#{{ submittedId }}</span>
                    </div>
                    <div class="success-item">
                        <span class="s-label">Nhân viên chủ trì</span>
                        <span class="s-value">{{ hostInfo.hostEmployeeName }}</span>
                    </div>
                </div>
                <p class="redirect-note">Tự động quay lại sau {{ countdown }} giây...</p>
            </div>

            <!-- FORM -->
            <div v-else class="register-card animate-in">
                <div class="card-header-info">
                    <h2>Đăng ký khách thăm quan</h2>
                    <div class="host-info-card">
                        <template v-if="hostInfo.hostFaceImageUrl">
                            <img :src="API_BASE + hostInfo.hostFaceImageUrl" class="host-avatar avatar-img" @error="$event.target.style.display = 'none'" />
                        </template>
                        <template v-else>
                            <div class="host-avatar">
                                {{ getInitials(hostInfo.hostEmployeeName) }}
                            </div>
                        </template>
                        <div class="host-details">
                            <span class="host-name">{{ hostInfo.hostEmployeeName }}</span>
                            <span v-if="hostInfo.hostPositionName || hostInfo.hostDepartmentName" class="host-role">
                                {{ hostInfo.hostPositionName }}<span v-if="hostInfo.hostPositionName && hostInfo.hostDepartmentName"> • </span>{{ hostInfo.hostDepartmentName }}
                            </span>
                            <div class="host-contact">
                                <span v-if="hostInfo.hostEmployeePhone" class="host-contact-item">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 13px; height: 13px;"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/></svg>
                                    {{ hostInfo.hostEmployeePhone }}
                                </span>
                                <span v-if="hostInfo.hostEmployeeEmail" class="host-contact-item">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 13px; height: 13px;"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                                    {{ hostInfo.hostEmployeeEmail }}
                                </span>
                                <span v-if="hostInfo.hostLicensePlates && hostInfo.hostLicensePlates.length > 0" class="host-contact-item" style="width: 100%;">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 13px; height: 13px;">
                                        <rect x="3" y="12" width="18" height="6" rx="2" ry="2"></rect>
                                        <path d="M5 12l2-4h10l2 4"></path>
                                        <circle cx="7" cy="18" r="1.5"></circle>
                                        <circle cx="17" cy="18" r="1.5"></circle>
                                    </svg>
                                    {{ hostInfo.hostLicensePlates.join(' • ') }}
                                </span>
                            </div>
                        </div>
                    </div>
                    <p class="expiry-note">Link hết hạn: {{ formatDateTime(hostInfo.expiredAt) }}</p>
                </div>

                <!-- Step indicators -->
                <div class="steps">
                    <div class="step" :class="{ active: currentStep >= 1, done: currentStep > 1 }">
                        <div class="step-num">{{ currentStep > 1 ? '✓' : '1' }}</div>
                        <span>Thông tin chính</span>
                    </div>
                    <div class="step-line" :class="{ active: currentStep > 1 }"></div>
                    <div class="step" :class="{ active: currentStep >= 2, done: currentStep > 2 }">
                        <div class="step-num">{{ currentStep > 2 ? '✓' : '2' }}</div>
                        <span>Thông tin đoàn</span>
                    </div>
                </div>

                <!-- Step 1: Main info -->
                <div v-show="currentStep === 1" class="step-content">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Họ và tên *</label>
                            <input v-model="form.fullName" type="text" placeholder="Nguyễn Văn An"
                                @input="runNameValidation"
                                @blur="nameValidation.touched = true; runNameValidation()"
                                :class="{ 'input-error': nameValidation.touched && !nameValidation.isValid && form.fullName.length >= 2, 'input-success': nameValidation.isValid }" />
                            <div v-if="nameValidation.touched && form.fullName.length >= 2" class="name-feedback">
                                <span v-if="nameValidation.isValid" class="feedback-success">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>
                                    Hợp lệ
                                </span>
                                <span v-else class="feedback-error">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6"/><path d="M9 9l6 6"/></svg>
                                    {{ nameValidation.error }}
                                </span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Số điện thoại</label>
                            <input v-model="form.phone" type="tel" placeholder="0901234567" />
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Biển số xe *</label>
                        <div class="combo-box-wrapper" style="position: relative;">
                            <input v-model="form.expectedLicensePlate" type="text" placeholder="VD: 36H3-12389"
                                @input="onGuestPlateInput" 
                                @focus="showPlateDropdown = true"
                                @blur="showPlateDropdown = false"
                                :class="{ 'input-error': plateValidation.touched && !plateValidation.isValid && form.expectedLicensePlate.length >= 3, 'input-success': plateValidation.isValid }"
                                maxlength="12" 
                                style="text-transform: uppercase; width: 100%; padding-right: 40px;" />
                            
                            <div v-if="hostInfo.hostLicensePlates && hostInfo.hostLicensePlates.length > 0" 
                                class="combo-icon" 
                                @mousedown.prevent="showPlateDropdown = !showPlateDropdown">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                            </div>
                            
                            <div v-if="showPlateDropdown && hostInfo.hostLicensePlates && hostInfo.hostLicensePlates.length > 0" class="combo-dropdown">
                                <div class="combo-header">Biển số xe đã đăng ký</div>
                                <div 
                                    v-for="(plate, idx) in hostInfo.hostLicensePlates" 
                                    :key="idx" 
                                    class="combo-item"
                                    :class="{ active: form.expectedLicensePlate === plate }"
                                    @mousedown.prevent="selectPlate(plate)"
                                >
                                    {{ plate }}
                                </div>
                            </div>
                        </div>
                        <div v-if="plateValidation.touched" class="plate-feedback">
                            <span v-if="plateValidation.isValid" class="feedback-success">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>
                                Hợp lệ — {{ plateValidation.typeLabel }}
                                <span v-if="plateValidation.corrected" class="feedback-corrected">(đã sửa: {{ plateValidation.cleanedPlate }})</span>
                            </span>
                            <span v-else-if="form.expectedLicensePlate.length >= 3" class="feedback-error">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6"/><path d="M9 9l6 6"/></svg>
                                Biển số không hợp lệ
                            </span>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Thời gian vào *</label>
                            <input v-model="form.expectedTimeIn" type="datetime-local" />
                        </div>
                        <div class="form-group">
                            <label>Thời gian ra *</label>
                            <input v-model="form.expectedTimeOut" type="datetime-local" />
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Số người trong đoàn *</label>
                        <input v-model.number="form.numberOfVisitors" type="number" min="1" max="50" />
                    </div>

                    <div class="form-actions">
                        <button class="btn btn-primary" @click="goToStep2"
                            :disabled="!form.fullName || !form.expectedLicensePlate || !form.expectedTimeIn || !form.expectedTimeOut || (plateValidation.touched && !plateValidation.isValid) || (nameValidation.touched && !nameValidation.isValid)">
                            Tiếp theo
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                style="width: 16px; height: 16px;">
                                <path d="M5 12h14" />
                                <path d="M12 5l7 7-7 7" />
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Step 2: Visitors -->
                <div v-show="currentStep === 2" class="step-content">
                    <p class="step-desc">Thêm thông tin từng người trong đoàn (tùy chọn)</p>

                    <div v-for="(v, i) in form.visitors" :key="i" class="visitor-form-card">
                        <div class="visitor-form-header">
                            <span class="visitor-num">Khách {{ i + 1 }}</span>
                            <button v-if="form.visitors.length > 1" class="btn-remove" @click="removeVisitor(i)">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                    style="width: 14px; height: 14px;">
                                    <path d="M18 6L6 18" />
                                    <path d="M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Họ tên *</label>
                                <input v-model="v.fullName" type="text" placeholder="Họ tên khách"
                                    @blur="runVisitorNameValidation(i)" 
                                    :class="{ 'input-error': v._nameError, 'input-success': v.fullName && !v._nameError }" />
                                <div v-if="v._nameError" class="name-feedback">
                                    <span class="feedback-error">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6"/><path d="M9 9l6 6"/></svg>
                                        {{ v._nameError }}
                                    </span>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Số CMND / CCCD</label>
                                <input v-model="v.idCardNumber" type="text" placeholder="012345678901" />
                            </div>
                        </div>
                    </div>

                    <button v-if="form.visitors.length < form.numberOfVisitors" class="btn-add-visitor"
                        @click="addVisitor">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                            style="width: 16px; height: 16px;">
                            <line x1="12" y1="5" x2="12" y2="19" />
                            <line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                        Thêm khách
                    </button>

                    <div class="form-actions step2-actions">
                        <button class="btn btn-secondary" @click="currentStep = 1">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                style="width: 16px; height: 16px;">
                                <path d="M19 12H5" />
                                <path d="M12 19l-7-7 7-7" />
                            </svg>
                            Quay lại
                        </button>
                        <button class="btn btn-primary" @click="handleSubmit" :disabled="isSubmitting">
                            {{ isSubmitting ? 'Đang gửi...' : 'Gửi đăng ký' }}
                        </button>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <p class="register-footer">V-Shield Security System © {{ new Date().getFullYear() }}</p>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { validateToken, submitRegistration } from '../services/preRegistrationApi'
import { optimizeAndValidatePlate, getVehicleTypeLabel } from '../utils/licensePlateValidator'
import { validateVietnameseName, normalizeVietnameseName } from '../utils/nameValidator'

const route = useRoute()
const router = useRouter()

// ── State ────────────────────────────────────────
const isValidating = ref(true)
const errorState = ref(false)
const errorMessage = ref('')
const hostInfo = reactive({
    hostEmployeeName: '',
    hostEmployeePhone: '',
    hostEmployeeEmail: '',
    hostDepartmentName: '',
    hostPositionName: '',
    hostFaceImageUrl: null,
    hostLicensePlates: [],
    expiredAt: null
})
const currentStep = ref(1)
const isSubmitting = ref(false)
const isSubmitted = ref(false)
const submittedId = ref(null)
const countdown = ref(5)
const showPlateDropdown = ref(false)

// License plate validation state
const plateValidation = reactive({
    touched: false,
    isValid: false,
    type: 'Unknown',
    typeLabel: '',
    cleanedPlate: '',
    corrected: false
})

// Name validation state
const nameValidation = reactive({
    touched: false,
    isValid: false,
    error: ''
})

function runNameValidation() {
    const val = form.fullName?.trim()
    if (!val) {
        nameValidation.touched = false
        nameValidation.isValid = false
        nameValidation.error = ''
        return
    }
    nameValidation.touched = true
    const result = validateVietnameseName(val)
    nameValidation.isValid = result.isValid
    nameValidation.error = result.error
}

function runVisitorNameValidation(index) {
    const visitor = form.visitors[index]
    if (!visitor) return
    const val = visitor.fullName?.trim()
    if (!val) {
        visitor._nameError = ''
        return
    }
    const result = validateVietnameseName(val)
    visitor._nameError = result.isValid ? '' : result.error
}

function runPlateValidation(value) {
    const val = value?.trim()
    if (!val) {
        plateValidation.touched = false
        plateValidation.isValid = false
        return
    }
    plateValidation.touched = true
    const result = optimizeAndValidatePlate(val)
    plateValidation.isValid = result.isValid
    plateValidation.type = result.type
    plateValidation.typeLabel = getVehicleTypeLabel(result.type)
    plateValidation.cleanedPlate = result.cleanedPlate
    plateValidation.corrected = result.cleanedPlate !== result.rawInput
}

const selectPlate = (plate) => {
    form.expectedLicensePlate = plate
    showPlateDropdown.value = false
    // Biển số từ dropdown host — luôn valid
    plateValidation.touched = true
    plateValidation.isValid = true
    plateValidation.type = 'Car'
    plateValidation.typeLabel = 'Đã đăng ký'
    plateValidation.cleanedPlate = plate
    plateValidation.corrected = false
}

const form = reactive({
    fullName: '',
    phone: '',
    expectedLicensePlate: '',
    expectedTimeIn: '',
    expectedTimeOut: '',
    numberOfVisitors: 1,
    visitors: [{ fullName: '', idCardNumber: '', expectedFaceImage: null, _nameError: '' }]
})

// ── Helpers ──────────────────────────────────────
const API_BASE = 'https://localhost:7107';

const getInitials = (name) => {
    if (!name) return '??'
    return name.split(' ').map(w => w[0]).join('').slice(-2).toUpperCase()
}

const onGuestPlateInput = (e) => {
    let val = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '')
    // Định dạng: 2 số tỉnh + 1-2 chữ cái + tùy chọn 1 số + dấu gạch + số còn lại
    const match = val.match(/^(\d{0,2})([A-Z]{0,2})(\d{0,1})(\d{0,5})$/)
    if (match) {
        let result = match[1] + match[2] + match[3]
        if (match[4]) {
            result += '-' + match[4]
        }
        form.expectedLicensePlate = result
    }
    // Validate realtime
    runPlateValidation(form.expectedLicensePlate)
}

const formatDateTime = (dt) => {
    if (!dt) return '—'
    const d = new Date(dt)
    const pad = (n) => String(n).padStart(2, '0')
    return `${pad(d.getHours())}:${pad(d.getMinutes())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`
}

// ── Steps ────────────────────────────────────────
const goToStep2 = () => {
    // Validate name
    runNameValidation()
    if (!nameValidation.isValid) {
        alert(nameValidation.error || 'Họ và tên không hợp lệ')
        return
    }
    // Apply normalized name
    form.fullName = normalizeVietnameseName(form.fullName)

    // Validate license plate
    if (form.expectedLicensePlate) {
        runPlateValidation(form.expectedLicensePlate)
        if (!plateValidation.isValid) {
            alert('Biển số xe không hợp lệ. VD hợp lệ: 51A-12345 (Ô tô), 29-A1 12345 (Xe máy)')
            return
        }
        // Apply cleaned plate if OCR corrected
        if (plateValidation.corrected) {
            form.expectedLicensePlate = plateValidation.cleanedPlate
        }
    }
    // Validate time
    if (new Date(form.expectedTimeOut) <= new Date(form.expectedTimeIn)) {
        alert('Thời gian ra phải sau thời gian vào!')
        return
    }
    // Ensure we have the right number of visitors
    while (form.visitors.length < form.numberOfVisitors) {
        form.visitors.push({ fullName: '', idCardNumber: '', expectedFaceImage: null, _nameError: '' })
    }
    while (form.visitors.length > form.numberOfVisitors) {
        form.visitors.pop()
    }
    currentStep.value = 2
}

const addVisitor = () => {
    form.visitors.push({ fullName: '', idCardNumber: '', expectedFaceImage: null, _nameError: '' })
}

const removeVisitor = (index) => {
    form.visitors.splice(index, 1)
}

// ── Submit ───────────────────────────────────────
const handleSubmit = async () => {
    // Validate visitor names
    const validVisitors = form.visitors.filter(v => v.fullName.trim())
    if (validVisitors.length === 0) {
        alert('Vui lòng điền tên ít nhất 1 khách trong đoàn')
        return
    }
    // Validate each visitor name
    let hasInvalidVisitor = false
    validVisitors.forEach((v, i) => {
        const result = validateVietnameseName(v.fullName)
        if (!result.isValid) {
            v._nameError = result.error
            hasInvalidVisitor = true
        } else {
            v.fullName = result.normalizedName
            v._nameError = ''
        }
    })
    if (hasInvalidVisitor) {
        alert('Vui lòng kiểm tra lại tên các khách trong đoàn')
        return
    }

    isSubmitting.value = true
    try {
        const data = {
            fullName: form.fullName,
            phone: form.phone || null,
            expectedLicensePlate: form.expectedLicensePlate,
            expectedTimeIn: new Date(form.expectedTimeIn).toISOString(),
            expectedTimeOut: new Date(form.expectedTimeOut).toISOString(),
            numberOfVisitors: form.numberOfVisitors,
            visitors: validVisitors.map(v => ({
                fullName: v.fullName,
                idCardNumber: v.idCardNumber || null,
                expectedFaceImage: v.expectedFaceImage || null
            }))
        }

        const res = await submitRegistration(route.params.token, data)
        submittedId.value = res.data.registrationId
        isSubmitted.value = true

        // Auto redirect back to pre-registration page after 5 seconds
        countdown.value = 5
        const timer = setInterval(() => {
            countdown.value--
            if (countdown.value <= 0) {
                clearInterval(timer)
                router.push({ name: 'PreRegistration' })
            }
        }, 1000)
    } catch (err) {
        console.error('Lỗi submit:', err)
        alert(err.response?.data?.message || 'Có lỗi xảy ra, vui lòng thử lại')
    } finally {
        isSubmitting.value = false
    }
}

const resetForm = () => {
    isSubmitted.value = false
    currentStep.value = 1
    form.fullName = hostInfo.hostEmployeeName || ''
    form.phone = hostInfo.hostEmployeePhone || ''
    form.expectedLicensePlate = (hostInfo.hostLicensePlates && hostInfo.hostLicensePlates.length > 0) ? hostInfo.hostLicensePlates[0] : ''
    form.expectedTimeIn = ''
    form.expectedTimeOut = ''
    form.numberOfVisitors = 1
    form.visitors = [{ fullName: '', idCardNumber: '', expectedFaceImage: null, _nameError: '' }]
}

// ── Init ─────────────────────────────────────────
onMounted(async () => {
    try {
        const token = route.params.token
        const res = await validateToken(token)
        hostInfo.hostEmployeeName = res.data.hostEmployeeName
        hostInfo.hostEmployeePhone = res.data.hostEmployeePhone
        hostInfo.hostEmployeeEmail = res.data.hostEmployeeEmail
        hostInfo.hostDepartmentName = res.data.hostDepartmentName
        hostInfo.hostPositionName = res.data.hostPositionName
        hostInfo.hostFaceImageUrl = res.data.hostFaceImageUrl
        hostInfo.hostLicensePlates = res.data.hostLicensePlates || []
        hostInfo.expiredAt = res.data.expiredAt

        // Tự động điền thông tin nhân viên chủ trì vào form
        form.fullName = res.data.hostEmployeeName || ''
        form.phone = res.data.hostEmployeePhone || ''
        
        // Auto fill if the user has plates
        if (hostInfo.hostLicensePlates.length > 0) {
            form.expectedLicensePlate = hostInfo.hostLicensePlates[0]
        }

        isValidating.value = false
    } catch (err) {
        isValidating.value = false
        errorState.value = true
        errorMessage.value = err.response?.data?.message || 'Link không hợp lệ hoặc đã hết hạn'
    }
})
</script>

<style scoped>
.guest-register {
    min-height: 100vh;
    background: var(--bg-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    position: relative;
    overflow: hidden;
}

/* Background decoration */
.bg-decoration {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
}

.bg-circle {
    position: absolute;
    border-radius: 50%;
    filter: blur(120px);
    opacity: 0.15;
}

.bg-circle.c1 {
    width: 600px;
    height: 600px;
    background: var(--accent-primary);
    top: -200px;
    right: -100px;
}

.bg-circle.c2 {
    width: 400px;
    height: 400px;
    background: var(--accent-secondary);
    bottom: -150px;
    left: -100px;
}

.bg-circle.c3 {
    width: 300px;
    height: 300px;
    background: var(--accent-success);
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.register-container {
    width: 100%;
    max-width: 600px;
    position: relative;
    z-index: 1;
}

/* Logo */
.register-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    justify-content: center;
    margin-bottom: 32px;
}

.register-logo .logo-icon {
    width: 40px;
    height: 40px;
    color: var(--accent-primary);
}

.register-logo .logo-icon svg {
    width: 100%;
    height: 100%;
}

.register-logo .logo-text {
    font-size: 1.5rem;
    font-weight: 800;
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Card */
.register-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-lg);
    padding: 36px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
}

.animate-in {
    animation: fadeIn 0.4s ease, slideUp 0.4s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Card header */
.card-header-info {
    margin-bottom: 28px;
}

.card-header-info h2 {
    font-size: 1.4rem;
    font-weight: 700;
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
}

.card-header-info p {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.card-header-info strong {
    color: var(--text-primary);
}

.expiry-note {
    font-size: 0.8rem !important;
    color: var(--text-muted) !important;
    margin-top: 12px;
}

/* Host employee info card */
.host-info-card {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 16px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    margin-top: 12px;
}

.host-avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 700;
    flex-shrink: 0;
}

.host-avatar.avatar-img {
    background: transparent;
    object-fit: cover;
}

.host-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
}

.host-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary);
}

.host-role {
    font-size: 0.8rem;
    color: var(--accent-primary);
    font-weight: 500;
}

.host-contact {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 2px;
}

.host-contact-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.78rem;
    color: var(--text-muted);
}

/* Combo Box */
.combo-box-wrapper {
    position: relative;
    width: 100%;
}

.combo-icon {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    width: 20px;
    height: 20px;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s ease;
}

.combo-icon:hover {
    color: var(--accent-primary);
}

.combo-dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    width: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    box-shadow: var(--shadow-lg);
    z-index: 100;
    max-height: 200px;
    overflow-y: auto;
    animation: fadeIn 0.15s ease;
}

.combo-header {
    padding: 8px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-input);
}

.combo-item {
    padding: 10px 12px;
    font-size: 0.9rem;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
}

.combo-item:hover {
    background: var(--bg-hover);
    color: var(--accent-primary);
}

.combo-item.active {
    background: rgba(16, 121, 196, 0.1);
    color: var(--accent-primary);
    font-weight: 600;
}

/* Steps */
.steps {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin-bottom: 30px;
}

.step {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-muted);
    font-size: 0.85rem;
    font-weight: 500;
    transition: color 0.3s ease;
}

.step.active {
    color: var(--accent-primary);
}

.step.done {
    color: var(--accent-success);
}

.step-num {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    background: var(--bg-input);
    border: 2px solid var(--border-color);
    transition: all 0.3s ease;
}

.step.active .step-num {
    background: rgba(16, 121, 196, 0.15);
    border-color: var(--accent-primary);
    color: var(--accent-primary);
}

.step.done .step-num {
    background: rgba(16, 185, 129, 0.15);
    border-color: var(--accent-success);
    color: var(--accent-success);
}

.step-line {
    width: 60px;
    height: 2px;
    background: var(--border-color);
    margin: 0 12px;
    transition: background 0.3s ease;
}

.step-line.active {
    background: var(--accent-primary);
}

/* Plate validation feedback */
.plate-feedback { margin-top: 4px; font-size: 0.82rem; display: flex; align-items: center; }
.name-feedback { margin-top: 4px; font-size: 0.82rem; display: flex; align-items: center; }
.feedback-success { display: inline-flex; align-items: center; gap: 5px; color: var(--accent-success); font-weight: 500; }
.feedback-error { display: inline-flex; align-items: center; gap: 5px; color: var(--accent-danger); font-weight: 500; }
.feedback-corrected { font-size: 0.78rem; color: var(--accent-primary); margin-left: 4px; font-style: italic; }
.input-error { border-color: var(--accent-danger) !important; box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.15) !important; }
.input-success { border-color: var(--accent-success) !important; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.15) !important; }

/* Step content */
.step-content {
    animation: fadeIn 0.3s ease;
}

.step-desc {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-bottom: 16px;
}

/* Visitor form card */
.visitor-form-card {
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    padding: 16px;
    margin-bottom: 12px;
}

.visitor-form-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.visitor-num {
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--accent-primary);
}

.btn-remove {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: transparent;
    color: var(--text-muted);
    transition: all 0.2s ease;
}

.btn-remove:hover {
    background: rgba(239, 68, 68, 0.15);
    color: var(--accent-danger);
}

.btn-add-visitor {
    width: 100%;
    padding: 12px;
    background: transparent;
    border: 2px dashed var(--border-color);
    border-radius: var(--border-radius-sm);
    color: var(--text-muted);
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.2s ease;
    margin-bottom: 20px;
}

.btn-add-visitor:hover {
    border-color: var(--accent-primary);
    color: var(--accent-primary);
    background: rgba(16, 121, 196, 0.05);
}

/* Form actions */
.form-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
    gap: 12px;
}

.step2-actions {
    justify-content: space-between;
}

.form-actions .btn {
    flex: 0 0 auto;
    width: auto;
}

/* Error / Success states */
.error-card,
.success-card {
    text-align: center;
}

.state-icon {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
}

.state-icon svg {
    width: 32px;
    height: 32px;
}

.state-icon.error {
    background: rgba(239, 68, 68, 0.15);
    color: var(--accent-danger);
}

.state-icon.success {
    background: rgba(16, 185, 129, 0.15);
    color: var(--accent-success);
}

.error-card h2,
.success-card h2 {
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 8px;
}

.state-msg {
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.6;
}

.success-details {
    margin-top: 24px;
    padding: 16px;
    background: var(--bg-input);
    border-radius: var(--border-radius-sm);
    border: 1px solid var(--border-color);
    display: inline-flex;
    gap: 32px;
}

.redirect-note {
    margin-top: 20px;
    font-size: 0.85rem;
    color: var(--text-muted);
    font-style: italic;
}

.success-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.s-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.s-value {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary);
}

/* Loading */
.loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 12px;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Footer */
.register-footer {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.8rem;
    margin-top: 24px;
}

/* Responsive */
@media (max-width: 600px) {
    .register-card {
        padding: 24px 20px;
    }

    .form-row {
        grid-template-columns: 1fr;
    }

    .steps span {
        display: none;
    }

    .success-details {
        flex-direction: column;
        gap: 16px;
    }
}
</style>
