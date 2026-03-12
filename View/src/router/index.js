import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, hasRole } from '../stores/auth'

import Login from '../pages/Login.vue'
import MainLayout from '../components/Layout/MainLayout.vue'
import Dashboard from '../pages/Dashboard.vue'
import Employees from '../pages/Employees.vue'
import Vehicles from '../pages/Vehicles.vue'
import AccessLogs from '../pages/AccessLogs.vue'
import Monitoring from '../pages/Monitoring.vue'
import Settings from '../pages/Settings.vue'
import UserManagement from '../pages/UserManagement.vue'
import DepartmentPosition from '../pages/DepartmentPosition.vue'


import FaceID from '../components/FaceCamera.vue'
import bienso from '../components/BienSoSecurity.vue'
import FaceVideo from '../components/FaceVideo.vue'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { guest: true },
    },
    {
        path: '/',
        component: MainLayout,
        meta: { requiresAuth: true },
        children: [
            { path: '', name: 'Dashboard', component: Dashboard },
            { path: 'employees', name: 'Employees', component: Employees },
            { path: 'vehicles', name: 'Vehicles', component: Vehicles },
            { path: 'access-logs', name: 'AccessLogs', component: AccessLogs },
            { path: 'monitoring', name: 'Monitoring', component: Monitoring },
            { path: 'settings', name: 'Settings', component: Settings },
            { path: 'FaceID', name: 'FaceID', component: FaceID },
            { path: 'bienso', name: 'bienso', component: bienso },
            { path: 'facevideo', name: 'facevideo', component: FaceVideo },
            {
                path: 'users',
                name: 'UserManagement',
                component: UserManagement,
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
    if (to.meta.guest && isLoggedIn()) {
        return next({ name: 'Dashboard' })
    }

    next()
})

export default router
