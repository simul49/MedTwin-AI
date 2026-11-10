import { defineStore } from 'pinia';
import { setLocale, type LocaleCode } from '@/i18n';

interface State {
  locale: LocaleCode;
  toasts: { id: number; message: string; tone: 'success' | 'error' | 'info' }[];
}

let toastId = 0;

export const useUiStore = defineStore('ui', {
  state: (): State => ({
    locale: (localStorage.getItem('medtwin.locale') as LocaleCode) || 'en',
    toasts: [],
  }),

  actions: {
    setLocale(code: LocaleCode) {
      this.locale = code;
      setLocale(code);
    },

    notify(message: string, tone: 'success' | 'error' | 'info' = 'info') {
      const id = ++toastId;
      this.toasts.push({ id, message, tone });
      setTimeout(() => {
        this.toasts = this.toasts.filter((t) => t.id !== id);
      }, 4000);
    },
  },
});
