import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, hasRole } from '../stores/auth'

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
import Exceptions from '../pages/Exceptions.vue'
import RegistrationLinks from '../pages/RegistrationLinks.vue'
import GuestProfiles from '../pages/GuestProfiles.vue'
import DeviceManagement from '../pages/DeviceManagement.vue'
import Biometrics from '../pages/Biometrics.vue'
import SystemCatalog from '../pages/SystemCatalog.vue'

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
            { path: '', redirect: { name: 'Dashboard' } },
            { path: 'dashboard', name: 'Dashboard', component: Dashboard },
            { path: 'monitoring', name: 'Monitoring', component: Monitoring },
            { path: 'access-logs', name: 'AccessLogs', component: AccessLogs },
            { path: 'exceptions', name: 'Exceptions', component: Exceptions },
            { path: 'pre-registrations', name: 'PreRegistration', component: PreRegistration },
            { path: 'registration-links', name: 'RegistrationLinks', component: RegistrationLinks },
            { path: 'guest-profiles', name: 'GuestProfiles', component: GuestProfiles },
            { path: 'about-project', name: 'AboutProject', component: AboutProject },
            { path: 'employees', name: 'Employees', component: Employees },
            { path: 'vehicles', name: 'Vehicles', component: Vehicles },
            { path: 'device-management', name: 'DeviceManagement', component: DeviceManagement },
            { path: 'biometrics', name: 'Biometrics', component: Biometrics },
            { path: 'settings', name: 'Settings', component: Settings },
            {
                path: 'users',
                name: 'UserManagement',
                component: UserManagement,
                meta: { requiresAdmin: true },
            },
            {
                path: 'system-catalog',
                name: 'SystemCatalog',
                component: SystemCatalog,
                meta: { requiresAdmin: true },
            },
            {
                path: 'departments-positions',
                name: 'DepartmentPosition',
                component: DepartmentPosition,
                meta: { requiresAdmin: true },
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
            return next({ name: 'Dashboard' })
        }
    }

    // Nếu đã đăng nhập mà vào trang login → redirect Dashboard
    // Nhưng cho phép truy cập trang đăng ký khách (GuestRegister) dù đã đăng nhập
    if (to.meta.guest && isLoggedIn() && to.name !== 'GuestRegister') {
        return next({ name: 'AboutProject' })
    }

    next()
})

export default router
