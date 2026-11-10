<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { ai } from '@/api/endpoints';
import type { Safety } from '@/api/types';
import AppCard from '@/components/ui/AppCard.vue';
import SafetyPanel from '@/components/ui/SafetyPanel.vue';

const { t } = useI18n();

const draft = ref('');
const result = ref<Safety | null>(null);
const evaluating = ref(false);
const error = ref<string | null>(null);

async function evaluate() {
  if (!draft.value.trim()) return;
  evaluating.value = true;
  error.value = null;
  try {
    result.value = await ai.evaluateSafety(draft.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    evaluating.value = false;
  }
}
</script>

<template>
  <div>
    <header class="mb-6">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('doctor.safetyEvaluate') }}</h1>
      <p class="muted mt-1">{{ t('trust.indicatorWarning') }}</p>
    </header>

    <div class="grid gap-6 lg:grid-cols-2">
      <AppCard :title="t('doctor.safetyEvaluate')">
        <textarea v-model="draft" class="input min-h-40" :placeholder="t('doctor.safetyEvaluate')" />
        <button class="btn-primary mt-3 w-full text-sm" :disabled="evaluating" @click="evaluate">
          {{ evaluating ? t('common.loading') : t('doctor.safetyEvaluate') }}
        </button>
        <p v-if="error" class="mt-2 text-sm text-rose-600">{{ error }}</p>
      </AppCard>

      <div>
        <SafetyPanel v-if="result" :safety="result" />
        <AppCard v-else :title="t('patient.trustScore')">
          <p class="muted">{{ t('common.none') }}</p>
        </AppCard>
      </div>
    </div>
  </div>
</template>
