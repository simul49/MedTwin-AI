<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';

const { t } = useI18n();
const auth = useAuthStore();
</script>

<template>
  <div class="container-page flex min-h-[60vh] flex-col items-center justify-center text-center">
    <p class="text-6xl font-black text-brand-600">403</p>
    <h1 class="mt-3 section-title">{{ t('common.error') }}</h1>
    <p class="muted mt-2 max-w-md">
      {{ t('doctor.subtitle') }}
    </p>
    <div class="mt-6 flex gap-3">
      <RouterLink :to="auth.homePath" class="btn-primary">{{ t('common.back') }}</RouterLink>
      <RouterLink to="/trust-safety" class="btn-secondary">{{ t('nav.trust') }}</RouterLink>
    </div>
  </div>
</template>
