import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, hasRole } from '../stores/auth'
import { authState } from '../stores/auth'

import Login from '../pages/Login.vue'
import MainLayout from '../components/Layout/MainLayout.vue'
import Dashboard from '../pages/Dashboard.vue'
import AboutProject from '../pages/AboutProject.vue'
import Employees from '../pages/Employees.vue'
import Vehicles from '../pages/Vehicles.vue'
import AccessLogs from '../pages/AccessLogs.vue'
import Monitoring from '../pages/Monitoring.vue'
import Settings from '../pages/Settings.vue'
import UserManagement from '../pages/UserManagement.vue'
import DepartmentPosition from '../pages/DepartmentPosition.vue'
import PreRegistration from '../pages/PreRegistration.vue'
import GuestRegister from '../pages/GuestRegister.vue'


import FaceID from '../components/FaceCamera.vue'
import bienso from '../components/BienSoSecurity.vue'
import FaceVideo from '../components/FaceVideo.vue'
import ThongHanh from '../components/ThongHanhQR.vue'
import Tao_QR_D from '../components/Tao_QR_D.vue'
import Scan_QR_D from '../components/Scan_QR_D.vue'
import Exceptions from '../pages/Exceptions.vue'
import RegistrationLinks from '../pages/RegistrationLinks.vue'
import GuestProfiles from '../pages/GuestProfiles.vue'
import DeviceManagement from '../pages/DeviceManagement.vue'
import Biometrics from '../pages/Biometrics.vue'
import SystemCatalog from '../pages/SystemCatalog.vue'

import SetCam from '../components/SetCam.vue'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { guest: true },
    },
    {
        path: '/register/:token',
        name: 'GuestRegister',
        component: GuestRegister,
        meta: { guest: true },
    },
    {
        path: '/',
        component: MainLayout,
        meta: { requiresAuth: true },
        children: [
            { path: '', redirect: to => {
                const role = authState.user?.role
                if (role === 'Staff') return { name: 'tao_qr_d' }
                return { name: 'Dashboard' }
            }},
            { path: 'dashboard', name: 'Dashboard', component: Dashboard, meta: { allowedRoles: ['Admin', 'BaoVe'] } },
            { path: 'monitoring', name: 'Monitoring', component: Monitoring, meta: { allowedRoles: ['Admin', 'BaoVe'], keepAlive: true } },
            { path: 'access-logs', name: 'AccessLogs', component: AccessLogs, meta: { allowedRoles: ['Admin', 'BaoVe'] } },
            { path: 'exceptions', name: 'Exceptions', component: Exceptions, meta: { allowedRoles: ['Admin', 'BaoVe'] } },
            { path: 'pre-registrations', name: 'PreRegistration', component: PreRegistration, meta: { allowedRoles: ['Admin'] } },
            { path: 'registration-links', name: 'RegistrationLinks', component: RegistrationLinks, meta: { allowedRoles: ['Admin'] } },
            { path: 'guest-profiles', name: 'GuestProfiles', component: GuestProfiles, meta: { allowedRoles: ['Admin'] } },
            { path: 'about-project', name: 'AboutProject', component: AboutProject },
            { path: 'FaceID', name: 'FaceID', component: FaceID, meta: { allowedRoles: ['Admin', 'BaoVe'], keepAlive: true } },
            { path: 'bienso', name: 'bienso', component: bienso, meta: { allowedRoles: ['Admin', 'BaoVe'], keepAlive: true } },
            { path: 'facevideo', name: 'facevideo', component: FaceVideo, meta: { allowedRoles: ['Admin', 'BaoVe'], keepAlive: true } },
            { path: 'thonghanh', name: 'thonghanh', component: ThongHanh, meta: { allowedRoles: ['Admin', 'BaoVe'], keepAlive: true } },
            { path: 'tao_qr_d', name: 'tao_qr_d', component: Tao_QR_D, meta: { allowedRoles: ['Admin', 'Staff', 'BaoVe'], keepAlive: true } },
            { path: 'scan_qr_d', name: 'scan_qr_d', component: Scan_QR_D, meta: { allowedRoles: ['Admin', 'BaoVe'], keepAlive: true } },
            { path: 'setcam', name: 'setcam', component: SetCam, meta: { allowedRoles: ['Admin', 'BaoVe'], keepAlive: true } },
            { path: 'employees', name: 'Employees', component: Employees, meta: { allowedRoles: ['Admin'] } },
            { path: 'vehicles', name: 'Vehicles', component: Vehicles, meta: { allowedRoles: ['Admin'] } },
            { path: 'device-management', name: 'DeviceManagement', component: DeviceManagement, meta: { allowedRoles: ['Admin'], keepAlive: true } },
            {
                path: 'system-catalog',
                name: 'SystemCatalog',
                component: SystemCatalog,
                meta: { requiresAdmin: true, allowedRoles: ['Admin'] },
            },
            {
                path: 'departments-positions',
                name: 'DepartmentPosition',
                component: DepartmentPosition,
                meta: { requiresAdmin: true, allowedRoles: ['Admin'] },
            },
        ],
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

// Navigation Guard
router.beforeEach((to, from, next) => {
    // Nếu route yêu cầu đăng nhập
    if (to.matched.some(r => r.meta.requiresAuth)) {
        if (!isLoggedIn()) {
            return next({ name: 'Login', query: { redirect: to.fullPath } })
        }
    }

    // Nếu route yêu cầu Admin
    if (to.matched.some(r => r.meta.requiresAdmin)) {
        if (!hasRole('Admin')) {
            const role = authState.user?.role
            if (role === 'Staff') return next({ name: 'tao_qr_d' })
            return next({ name: 'Dashboard' })
        }
    }

    // Kiểm tra allowedRoles
    const allowedRoles = to.matched.find(r => r.meta.allowedRoles)?.meta.allowedRoles
    if (allowedRoles) {
        const currentRole = authState.user?.role
        if (!allowedRoles.includes(currentRole)) {
            if (currentRole === 'Staff') return next({ name: 'tao_qr_d' })
            return next({ name: 'Dashboard' })
        }
    }

    // Nếu đã đăng nhập mà vào trang login → redirect
    // Nhưng cho phép truy cập trang đăng ký khách (GuestRegister) dù đã đăng nhập
    if (to.meta.guest && isLoggedIn() && to.name !== 'GuestRegister') {
        const role = authState.user?.role
        if (role === 'Staff') return next({ name: 'tao_qr_d' })
        return next({ name: 'Dashboard' })
    }

    next()
})

export default router
