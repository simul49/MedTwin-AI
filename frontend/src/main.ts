import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import { router } from './router';
import { i18n } from './i18n';
import { reveal } from './directives/reveal';
import './style.css';

createApp(App)
  .use(createPinia())
  .use(router)
  .use(i18n)
  .directive('reveal', reveal)
  .mount('#app');
