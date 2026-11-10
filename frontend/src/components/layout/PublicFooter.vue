<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>

<template>
  <footer class="mt-20 border-t border-ink-200 bg-white">
    <div class="container-page grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-4">
      <div class="lg:col-span-2">
        <div class="flex items-center gap-2">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-sm font-bold text-white">MT</span>
          <span class="text-lg font-extrabold text-brand-700">{{ t('brand.short') }}</span>
        </div>
        <p class="mt-3 font-semibold text-ink-900">{{ t('brand.full') }}</p>
        <p class="mt-1 max-w-md text-sm leading-relaxed text-ink-500">{{ t('footer.description') }}</p>
      </div>

      <div>
        <p class="text-sm font-semibold text-ink-900">{{ t('footer.product') }}</p>
        <ul class="mt-3 space-y-2 text-sm text-ink-600">
          <li><RouterLink class="hover:text-brand-700" to="/solutions">{{ t('nav.solutions') }}</RouterLink></li>
          <li><RouterLink class="hover:text-brand-700" to="/how-it-works">{{ t('nav.howItWorks') }}</RouterLink></li>
          <li><RouterLink class="hover:text-brand-700" to="/research">{{ t('nav.research') }}</RouterLink></li>
          <li><RouterLink class="hover:text-brand-700" to="/trust-safety">{{ t('nav.trust') }}</RouterLink></li>
        </ul>
      </div>

      <div>
        <p class="text-sm font-semibold text-ink-900">{{ t('footer.legal') }}</p>
        <ul class="mt-3 space-y-2 text-sm text-ink-600">
          <li><RouterLink class="hover:text-brand-700" to="/privacy">{{ t('legal.privacy') }}</RouterLink></li>
          <li><RouterLink class="hover:text-brand-700" to="/terms">{{ t('legal.terms') }}</RouterLink></li>
          <li><RouterLink class="hover:text-brand-700" to="/medical-disclaimer">{{ t('legal.medical') }}</RouterLink></li>
          <li><RouterLink class="hover:text-brand-700" to="/contact">{{ t('footer.contact') }}</RouterLink></li>
        </ul>
      </div>
    </div>

    <div class="border-t border-ink-100 bg-ink-50">
      <div class="container-page py-6">
        <p class="text-xs leading-relaxed text-ink-500">{{ t('footer.medicalNotice') }}</p>
        <p class="mt-3 text-xs text-ink-400">
          © {{ new Date().getFullYear() }} {{ t('brand.full') }} — {{ t('brand.tagline') }}. {{ t('footer.rights') }}
        </p>
      </div>
    </div>
  </footer>
</template>
