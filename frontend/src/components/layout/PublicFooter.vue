<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>

<template>
  <footer class="mt-20 bg-navy-700 text-white/90">
    <div class="container-page grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-4">
      <div class="lg:col-span-2">
        <div class="flex items-center gap-2">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-sm font-bold text-white">MT</span>
          <span class="text-lg font-extrabold text-white">{{ t('brand.short') }}</span>
        </div>
        <p class="mt-3 font-semibold text-white">{{ t('brand.full') }}</p>
        <p class="mt-1 max-w-md text-sm leading-relaxed text-brand-100/70">{{ t('footer.description') }}</p>
      </div>

      <div>
        <p class="text-sm font-semibold text-white">{{ t('footer.product') }}</p>
        <ul class="mt-3 space-y-2 text-sm text-brand-100/70">
          <li><RouterLink class="transition-colors hover:text-white" to="/solutions">{{ t('nav.solutions') }}</RouterLink></li>
          <li><RouterLink class="transition-colors hover:text-white" to="/how-it-works">{{ t('nav.howItWorks') }}</RouterLink></li>
          <li><RouterLink class="transition-colors hover:text-white" to="/research">{{ t('nav.research') }}</RouterLink></li>
          <li><RouterLink class="transition-colors hover:text-white" to="/trust-safety">{{ t('nav.trust') }}</RouterLink></li>
        </ul>
      </div>

      <div>
        <p class="text-sm font-semibold text-white">{{ t('footer.legal') }}</p>
        <ul class="mt-3 space-y-2 text-sm text-brand-100/70">
          <li><RouterLink class="transition-colors hover:text-white" to="/privacy">{{ t('legal.privacy') }}</RouterLink></li>
          <li><RouterLink class="transition-colors hover:text-white" to="/terms">{{ t('legal.terms') }}</RouterLink></li>
          <li><RouterLink class="transition-colors hover:text-white" to="/medical-disclaimer">{{ t('legal.medical') }}</RouterLink></li>
          <li><RouterLink class="transition-colors hover:text-white" to="/contact">{{ t('footer.contact') }}</RouterLink></li>
        </ul>
      </div>
    </div>

    <div class="border-t border-white/10 bg-navy-800">
      <div class="container-page py-6">
        <p class="text-xs leading-relaxed text-brand-100/60">{{ t('footer.medicalNotice') }}</p>
        <p class="mt-3 text-xs text-brand-100/50">
          © {{ new Date().getFullYear() }} {{ t('brand.full') }} — {{ t('brand.tagline') }}. {{ t('footer.rights') }}
        </p>
      </div>
    </div>
  </footer>
</template>
