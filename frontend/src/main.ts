import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import App from './App.vue'
import { THEME_STORAGE_KEY } from './constants'

const app = createApp(App)

const cachedTheme = localStorage.getItem(THEME_STORAGE_KEY)
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
const isDark = cachedTheme ? cachedTheme === 'dark' : prefersDark
document.documentElement.classList.toggle('dark', isDark)

app.use(ElementPlus)
app.mount('#app')
