import { createApp } from 'vue'
import { createPinia } from 'pinia'
import TDesign from 'tdesign-vue-next'
import VueApexCharts from 'vue3-apexcharts'
import router from './router'
import App from './App.vue'

// TDesign 样式
import 'tdesign-vue-next/es/style/index.css'
import './assets/styles/main.less'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(TDesign)
app.use(VueApexCharts)

app.mount('#app')
