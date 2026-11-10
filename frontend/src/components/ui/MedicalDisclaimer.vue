<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
defineProps<{ compact?: boolean }>();
</script>

<template>
  <div class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
    <p class="font-semibold">{{ t('footer.medicalNoticeTitle', 'Medical disclaimer') }}</p>
    <p v-if="!compact" class="mt-1 leading-relaxed">{{ t('brand.disclaimer') }}</p>
  </div>
</template>
