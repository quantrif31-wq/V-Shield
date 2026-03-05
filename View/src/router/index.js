import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../pages/Dashboard.vue'
import Employees from '../pages/Employees.vue'
import Vehicles from '../pages/Vehicles.vue'
import AccessLogs from '../pages/AccessLogs.vue'
import Monitoring from '../pages/Monitoring.vue'
import Settings from '../pages/Settings.vue'

const routes = [
    { path: '/', name: 'Dashboard', component: Dashboard },
    { path: '/employees', name: 'Employees', component: Employees },
    { path: '/vehicles', name: 'Vehicles', component: Vehicles },
    { path: '/access-logs', name: 'AccessLogs', component: AccessLogs },
    { path: '/monitoring', name: 'Monitoring', component: Monitoring },
    { path: '/settings', name: 'Settings', component: Settings },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router
