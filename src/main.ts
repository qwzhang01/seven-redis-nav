import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';

// 全局样式 — 顺序重要
import './styles/tokens.css';
import './styles/reset.css';
import './styles/globals.css';

// RemixIcon
import 'remixicon/fonts/remixicon.css';

const app = createApp(App);
app.use(createPinia());
app.mount('#app');
