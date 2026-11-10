<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>

<template>
  <div class="container-page flex min-h-[60vh] flex-col items-center justify-center text-center">
    <p class="text-6xl font-black text-brand-600">404</p>
    <h1 class="mt-3 section-title">{{ t('common.empty') }}</h1>
    <RouterLink to="/" class="btn-primary mt-6">{{ t('common.back') }}</RouterLink>
  </div>
</template>
