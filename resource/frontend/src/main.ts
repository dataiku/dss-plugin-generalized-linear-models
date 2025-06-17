import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'

import { Quasar, Notify, Loading, Dialog} from "quasar";
import "@quasar/extras/material-icons/material-icons.css";
import "@quasar/extras/material-icons-outlined/material-icons-outlined.css";
import "@quasar/extras/material-icons-round/material-icons-round.css";
import "@quasar/extras/mdi-v6/mdi-v6.css";
import "quasar/src/css/index.sass";
import "quasar-ui-bs/dist/quasar-ui-bs.css";
import "vite/modulepreload-polyfill";
import "./assets/fonts/fonts.scss";
import { QuasarBs } from "quasar-ui-bs";
import { createPinia } from "pinia";

const myApp = createApp(App)

myApp.use(Quasar, {
    plugins: {
        Notify,
        Loading,
        Dialog
    }
})
myApp.use(QuasarBs);
myApp.use(createPinia());
myApp.mount('#app')