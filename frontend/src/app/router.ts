import { createRouter, createWebHistory } from 'vue-router'

import RobotControlView from '../robot-control/views/RobotControlView.vue'
import DatabaseView from '../database/views/DatabaseView.vue'
import MachineLearningView from '../ml/views/MachineLearningView.vue'
import ChatbotView from '../chatbot/views/ChatbotView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/robot-control' },
    { path: '/robot-control', component: RobotControlView },
    { path: '/database', component: DatabaseView },
    { path: '/ml', component: MachineLearningView },
    { path: '/chatbot', component: ChatbotView },
  ],
})

export default router
