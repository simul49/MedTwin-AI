import { createI18n } from 'vue-i18n';
import en from './en';
import zh from './zh';

export const SUPPORTED_LOCALES = [
  { code: 'en', label: 'EN' },
] as const;

export type LocaleCode = (typeof SUPPORTED_LOCALES)[number]['code'];

// The platform is English-only by product decision: no auto-detection from the
// browser/OS language and no 中文 option — the UI is always English.
function initialLocale(): LocaleCode {
  localStorage.removeItem(STORAGE_KEY);
  return 'en';
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
