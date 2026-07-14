import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  // ========== 公开路由 ==========
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { public: true, title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { public: true, title: '注册' }
  },

  // ========== 市民端 ==========
  {
    path: '/citizen',
    component: () => import('@/layouts/CitizenLayout.vue'),
    meta: { requiresAuth: true, roles: ['citizen'] },
    children: [
      { path: '', redirect: '/citizen/home' },
      {
        path: 'home',
        name: 'CitizenHome',
        component: () => import('@/views/citizen/Home.vue'),
        meta: { title: '首页', keepAlive: true }
      },
      {
        path: 'report',
        name: 'CitizenReport',
        component: () => import('@/views/citizen/Report.vue'),
        meta: { title: '随手拍举报' }
      },
      {
        path: 'my-reports',
        name: 'CitizenMyReports',
        component: () => import('@/views/citizen/MyReports.vue'),
        meta: { title: '举报进度', keepAlive: true }
      },
      {
        path: 'vehicles',
        name: 'CitizenVehicles',
        component: () => import('@/views/citizen/VehicleBinding.vue'),
        meta: { title: '车辆绑定', keepAlive: true }
      },
      {
        path: 'my-violations',
        name: 'CitizenMyViolations',
        component: () => import('@/views/citizen/MyViolations.vue'),
        meta: { title: '违章查询', keepAlive: true }
      },
      {
        path: 'profile',
        name: 'CitizenProfile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人信息' }
      }
    ]
  },

  // ========== 审核工作台（交管工作人员）==========
  {
    path: '/review',
    component: () => import('@/layouts/ReviewLayout.vue'),
    meta: { requiresAuth: true, roles: ['reviewer', 'admin'] },
    children: [
      { path: '', redirect: '/review/workbench' },
      {
        path: 'workbench',
        name: 'ReviewWorkbench',
        component: () => import('@/views/review/Workbench.vue'),
        meta: { title: '审核工作台', keepAlive: true }
      },
      {
        path: 'case/:id',
        name: 'CaseDetail',
        component: () => import('@/views/review/CaseDetail.vue'),
        meta: { title: '案件详情' }
      },
      {
        path: 'violations',
        name: 'ReviewViolations',
        component: () => import('@/views/review/ViolationList.vue'),
        meta: { title: '违章列表', keepAlive: true }
      },
      {
        path: 'upload',
        name: 'ReviewUpload',
        component: () => import('@/views/review/ImageUpload.vue'),
        meta: { title: '证据上传', keepAlive: true }
      },
      {
        path: 'profile',
        name: 'ReviewProfile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人信息' }
      }
    ]
  },

  // ========== 统计分析台 ==========
  {
    path: '/stats',
    component: () => import('@/layouts/ReviewLayout.vue'),
    meta: { requiresAuth: true, roles: ['reviewer', 'admin'] },
    children: [
      {
        path: '',
        name: 'StatsDashboard',
        component: () => import('@/views/stats/Dashboard.vue'),
        meta: { title: '统计分析', keepAlive: true }
      },
      {
        path: 'report',
        name: 'StatsReport',
        component: () => import('@/views/stats/Report.vue'),
        meta: { title: '分析报告' }
      }
    ]
  },

  // ========== 系统管理端（超级管理员）==========
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      { path: '', redirect: '/admin/stats' },
      {
        path: 'stats',
        name: 'AdminStats',
        component: () => import('@/views/stats/Dashboard.vue'),
        meta: { title: '统计分析', keepAlive: true }
      },
      {
        path: 'stats/report',
        name: 'AdminStatsReport',
        component: () => import('@/views/stats/Report.vue'),
        meta: { title: '分析报告' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManage.vue'),
        meta: { title: '用户管理', keepAlive: true }
      },
      {
        path: 'cameras',
        name: 'AdminCameras',
        component: () => import('@/views/admin/CameraManage.vue'),
        meta: { title: '摄像头管理', keepAlive: true }
      },
      {
        path: 'rules',
        name: 'AdminRules',
        component: () => import('@/views/admin/RuleConfig.vue'),
        meta: { title: '违章规则', keepAlive: true }
      },
      {
        path: 'sms-templates',
        name: 'AdminSms',
        component: () => import('@/views/admin/SmsTemplate.vue'),
        meta: { title: '短信模板' }
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/AuditLog.vue'),
        meta: { title: '操作日志', keepAlive: true }
      },
      {
        path: 'announcements',
        name: 'AdminAnnouncements',
        component: () => import('@/views/admin/Announcement.vue'),
        meta: { title: '公告管理', keepAlive: true }
      },
      {
        path: 'violations/upload',
        name: 'AdminViolationUpload',
        component: () => import('@/views/admin/ViolationUpload.vue'),
        meta: { title: '违章上传' }
      },
      {
        path: 'violations/review',
        name: 'AdminCaseReview',
        component: () => import('@/views/review/Workbench.vue'),
        meta: { title: '案件审核' }
      },
      {
        path: 'violations/:id',
        name: 'AdminViolationDetail',
        component: () => import('@/views/review/CaseDetail.vue'),
        meta: { title: '违章详情' }
      },
      {
        path: 'violations',
        name: 'AdminViolationList',
        component: () => import('@/views/admin/ViolationList.vue'),
        meta: { title: '违章列表', keepAlive: true }
      },
      {
        path: 'vehicles',
        name: 'AdminVehicles',
        component: () => import('@/views/admin/VehicleList.vue'),
        meta: { title: '车辆管理', keepAlive: true }
      },
      {
        path: 'profile',
        name: 'AdminProfile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人信息' }
      }
    ]
  },

  // 根路径
  { path: '/', redirect: '/login' },
  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ========== 路由守卫 ==========
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.public) {
    if (userStore.token && to.path === '/login') {
      return next(userStore.homePath)
    }
    return next()
  }

  if (!userStore.token) {
    return next('/login')
  }

  if (to.meta.roles && !to.meta.roles.includes(userStore.role)) {
    return next(userStore.homePath)
  }

  next()
})

export default router
