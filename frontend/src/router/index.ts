import { createRouter, createWebHistory } from 'vue-router'
import RobotControlView from '../views/RobotControlView.vue'
import DatabaseView from '../views/DatabaseView.vue'
import MLView from '../views/MLView.vue'
import ChatbotView from '../views/ChatbotView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/robot-control'
    },
    {
      path: '/robot-control',
      name: 'robot-control',
      component: RobotControlView
    },
    {
      path: '/database',
      name: 'database',
      component: DatabaseView
    },
    {
      path: '/machine-learning',
      name: 'machine-learning',
      component: MLView
    },
    {
      path: '/chatbot',
      name: 'chatbot',
      component: ChatbotView
    }
  ]
})

export default router
