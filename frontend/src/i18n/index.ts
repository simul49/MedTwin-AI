import { createI18n } from 'vue-i18n';
import en from './en';
import zh from './zh';

export const SUPPORTED_LOCALES = [
  { code: 'en', label: 'EN' },
  { code: 'zh', label: '中文' },
] as const;

export type LocaleCode = (typeof SUPPORTED_LOCALES)[number]['code'];

const STORAGE_KEY = 'medtwin.locale';

function initialLocale(): LocaleCode {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'en' || stored === 'zh') return stored;
  return navigator.language?.toLowerCase().startsWith('zh') ? 'zh' : 'en';
}

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale(),
  fallbackLocale: 'en',
  messages: { en, zh },
});

export function setLocale(code: LocaleCode) {
  i18n.global.locale.value = code;
  localStorage.setItem(STORAGE_KEY, code);
  document.documentElement.lang = code;
}

export function currentLocale(): LocaleCode {
  return i18n.global.locale.value as LocaleCode;
}

document.documentElement.lang = initialLocale();
