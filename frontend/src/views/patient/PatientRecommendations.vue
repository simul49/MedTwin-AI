<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { ai } from '@/api/endpoints';
import type { Recommendation } from '@/api/types';

const { t } = useI18n();

const items = ref<Recommendation[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const busy = ref<string | null>(null);

const TYPES: Record<string, { title: string; hint: string; tone: string; icon: string }> = {
  EDUCATION: {
    title: 'Learn about your health',
    hint: 'Short explanations grounded in approved material',
    tone: 'bg-sky-50 text-sky-700',
    icon: 'M4 4h16v16H4zM8 9h8M8 13h8',
  },
  NEXT_STEP: {
    title: 'Suggested next steps',
    hint: 'Actions that keep your records trustworthy',
    tone: 'bg-brand-50 text-brand-700',
    icon: 'M5 13l4 4L19 7',
  },
  QUESTION_TO_ASK: {
    title: 'Questions for your clinician',
    hint: 'Topics worth raising at your next visit',
    tone: 'bg-violet-50 text-violet-700',
    icon: 'M4 5h16v11H9l-5 4z',
  },
  LIFESTYLE: {
    title: 'Everyday habits',
    hint: 'General, non-personalised wellbeing information',
    tone: 'bg-amber-50 text-amber-700',
    icon: 'M12 21s-7-4.5-7-10a4 4 0 017-2.6A4 4 0 0119 11c0 5.5-7 10-7 10z',
  },
};

function meta(type: string) {
  return TYPES[type] ?? {
    title: type.replaceAll('_', ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase()),
    hint: 'Personalised suggestions',
    tone: 'bg-surface-100 text-ink-600',
    icon: 'M12 3l2.6 5.6 6.1.8-4.5 4.3 1.1 6-5.3-3-5.3 3 1.1-6L3.3 9.4l6.1-.8z',
  };
}

const grouped = computed(() => {
  const map: Record<string, Recommendation[]> = {};
  for (const item of items.value) (map[item.type] ??= []).push(item);
  return Object.entries(map).sort((a, b) => {
    const order = ['NEXT_STEP', 'QUESTION_TO_ASK', 'EDUCATION', 'LIFESTYLE'];
    const ai = order.indexOf(a[0]);
    const bi = order.indexOf(b[0]);
    return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi);
  });
});

function basisText(item: Recommendation): string {
  if (item.basisText) return item.basisText;
  const b = item.basis ?? {};
  const parts: string[] = [];
  if (typeof b.condition === 'string') parts.push(`Related to your record: ${b.condition}`);
  if (typeof b.flag === 'string') parts.push(`A recent measurement was flagged ${b.flag.toLowerCase()}`);
  if (typeof b.medicationCount === 'number') parts.push(`Based on ${b.medicationCount} active medications`);
  if (typeof b.unverifiedCount === 'number') parts.push(`${b.unverifiedCount} record(s) still need confirmation`);
  return parts.join(' · ');
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    items.value = (await ai.recommendations()).results;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function respond(item: Recommendation, decision: 'ACCEPTED' | 'DISMISSED') {
  busy.value = item.id;
  try {
    await ai.recommendationFeedback(item.id, decision);
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    busy.value = null;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Personalised guidance</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">{{ t('patient.recommendationsTitle') }}</h1>
        <p class="mt-2 max-w-2xl text-[14px] leading-relaxed text-ink-500">{{ t('patient.recommendationsHint') }}</p>
      </div>
      <span class="chip border border-ink-200 bg-white text-ink-600">{{ items.length }} suggestions</span>
    </div>

    <div class="dash-info mb-5">
      These are educational prompts derived from your own records — not medical advice. Keep what is useful and dismiss anything that does not apply.
    </div>

    <p v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-[13px] text-rose-700">{{ error }}</p>
    <div v-else-if="loading" class="h-48 animate-pulse rounded-2xl bg-ink-100" />
    <div v-else-if="!items.length" class="dash-card px-5 py-14 text-center">
      <p class="text-[15px] font-semibold text-ink-700">Nothing new for you right now</p>
      <p class="mt-1 text-[12px] text-ink-400">Suggestions appear as new records and measurements are added.</p>
    </div>

    <div v-else class="space-y-6">
      <section v-for="[type, group] in grouped" :key="type">
        <div class="mb-3 flex items-center gap-3">
          <span class="dash-icon-tile" :class="meta(type).tone">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path :d="meta(type).icon" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div>
            <h2 class="dash-section-title">{{ meta(type).title }}</h2>
            <p class="dash-section-sub mt-0.5">{{ meta(type).hint }}</p>
          </div>
          <span class="ml-auto chip bg-surface-100 text-ink-500">{{ group.length }}</span>
        </div>

        <div class="grid gap-4" :class="group.length > 1 ? 'lg:grid-cols-2' : ''">
          <article
            v-for="item in group"
            :key="item.id"
            class="dash-card flex flex-col p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lift"
          >
            <div class="flex items-start justify-between gap-3">
              <h3 class="text-[15px] font-bold leading-snug text-ink-900">{{ item.title }}</h3>
              <span class="chip shrink-0" :class="meta(type).tone">{{ meta(type).title.split(' ')[0] }}</span>
            </div>
            <p class="mt-2 flex-1 text-[13px] leading-relaxed text-ink-600">{{ item.body }}</p>
            <p v-if="basisText(item)" class="mt-3 border-t border-ink-100 pt-3 text-[11px] leading-relaxed text-ink-400">
              {{ basisText(item) }}
            </p>
            <div class="mt-4 flex gap-2">
              <button class="dash-btn px-4 py-2 text-xs" :disabled="busy === item.id" @click="respond(item, 'ACCEPTED')">
                Keep
              </button>
              <button class="btn-secondary px-4 py-2 text-xs" :disabled="busy === item.id" @click="respond(item, 'DISMISSED')">
                Dismiss
              </button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>
