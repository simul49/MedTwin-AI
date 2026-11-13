<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ai } from '@/api/endpoints';
import type { Recommendation } from '@/api/types';

const { t } = useI18n();

const items = ref<Recommendation[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const busy = ref<string | null>(null);
const kept = ref(0);
const dismissed = ref(0);
const copiedId = ref<string | null>(null);

const totalLoaded = ref(0);
const handled = computed(() => kept.value + dismissed.value);
const progressPct = computed(() =>
  totalLoaded.value ? Math.round((handled.value / totalLoaded.value) * 100) : 0,
);

const TYPES: Record<string, { title: string; hint: string; tone: string; icon: string }> = {
  EDUCATION: {
    title: 'Learn about your health',
    hint: 'Short explanations grounded in approved material',
    tone: 'bg-brand-50 text-brand-700',
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
    tone: 'bg-lavender-light text-lavender-dark',
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

/** Focus level derived from why this suggestion exists. */
function priority(item: Recommendation): 'FOCUS' | 'ACTION' | null {
  const b = item.basis ?? {};
  const flag = typeof b.flag === 'string' ? b.flag.toUpperCase() : '';
  if (flag === 'HIGH' || flag === 'CRITICAL') return 'FOCUS';
  if (typeof b.unverifiedCount === 'number' && b.unverifiedCount > 0) return 'ACTION';
  return null;
}

/** The most useful one-click follow-up for this card. */
function actionFor(item: Recommendation): { label: string; to: string } | null {
  const question = `${item.title}. ${item.body}`.slice(0, 400);
  if (item.type === 'QUESTION_TO_ASK') return { label: 'Ask the AI assistant', to: `/patient/assistant?q=${encodeURIComponent(question)}` };
  if (item.type === 'EDUCATION') return { label: 'Learn more with AI', to: `/patient/assistant?q=${encodeURIComponent(item.title)}` };
  if (item.type === 'NEXT_STEP') {
    const b = item.basis ?? {};
    if (typeof b.unverifiedCount === 'number' && b.unverifiedCount > 0) return { label: 'Review records', to: '/patient/records' };
    return { label: 'Discuss with AI', to: `/patient/assistant?q=${encodeURIComponent(question)}` };
  }
  if (item.type === 'LIFESTYLE') return { label: 'Explore with AI', to: `/patient/assistant?q=${encodeURIComponent(item.title)}` };
  return null;
}

const grouped = computed(() => {
  const map: Record<string, Recommendation[]> = {};
  for (const item of items.value) (map[item.type] ??= []).push(item);
  // Highest-impact groups first; inside a group, focus/action items float up.
  const order = ['NEXT_STEP', 'QUESTION_TO_ASK', 'EDUCATION', 'LIFESTYLE'];
  return Object.entries(map)
    .sort((a, b) => {
      const ai = order.indexOf(a[0]);
      const bi = order.indexOf(b[0]);
      return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi);
    })
    .map(([type, group]) => [
      type,
      [...group].sort((a, b) => (priority(b) ? 1 : 0) - (priority(a) ? 1 : 0)),
    ] as [string, Recommendation[]]);
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

/** Uniform footer for cards without a data-derived basis. */
function footerNote(type: string): string {
  if (type === 'LIFESTYLE') return 'General wellbeing guidance — applies to everyone.';
  if (type === 'FOLLOW_UP') return 'Based on your active medication list.';
  return 'Derived from your Digital Twin records.';
}

async function copyItem(item: Recommendation) {
  try {
    await navigator.clipboard.writeText(`${item.title}\n\n${item.body}`);
    copiedId.value = item.id;
    setTimeout(() => (copiedId.value = null), 1800);
  } catch {
    /* clipboard unavailable — ignore */
  }
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    items.value = (await ai.recommendations()).results;
    totalLoaded.value = items.value.length;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

/** Optimistic: update the row in place, refetch only on failure. */
async function respond(item: Recommendation, decision: 'ACCEPTED' | 'DISMISSED') {
  busy.value = item.id;
  try {
    await ai.recommendationFeedback(item.id, decision);
    items.value = items.value.filter((r) => r.id !== item.id);
    if (decision === 'ACCEPTED') kept.value += 1;
    else dismissed.value += 1;
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
    <div class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">Personalised guidance</p>
        <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">{{ t('patient.recommendationsTitle') }}</h1>
        <p class="mt-1.5 max-w-2xl text-[13.5px] leading-relaxed text-ink-500">{{ t('patient.recommendationsHint') }}</p>
      </div>
      <span class="chip border border-ink-200 bg-white text-ink-600">{{ items.length }} suggestions</span>
    </div>

    <div class="dash-info mb-4">
      These are educational prompts derived from your own records — not medical advice. Keep what is useful and dismiss anything that does not apply.
    </div>

    <p v-if="error" class="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-[13px] text-rose-700">{{ error }}</p>

    <div v-else-if="loading" class="shimmer h-48 animate-pulse rounded-2xl bg-ink-100" />

    <div v-else-if="!items.length && !handled" class="dash-card px-5 py-14 text-center">
      <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50">
        <svg class="h-5 w-5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </span>
      <p class="mt-3 text-[15px] font-semibold text-ink-700">Nothing new for you right now</p>
      <p class="mt-1 text-[12px] text-ink-400">Suggestions appear as new records and measurements are added.</p>
    </div>

    <template v-else>
      <!-- Progress strip -->
      <div v-if="totalLoaded" class="dash-card mb-5 px-4 py-3">
        <div class="flex flex-wrap items-center justify-between gap-2.5">
          <div class="flex items-center gap-2.5">
            <span class="dash-icon-tile h-9 w-9">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M4 19V9m6 10V5m6 14v-7" stroke-linecap="round" />
              </svg>
            </span>
            <div>
              <p class="text-[12.5px] font-bold text-ink-900">Your review progress</p>
              <p class="text-[11px] text-ink-400">{{ handled }} of {{ totalLoaded }} suggestions handled this visit</p>
            </div>
          </div>
          <div class="flex items-center gap-3 text-[11px] font-semibold">
            <span class="flex items-center gap-1.5 text-brand-700"><span class="h-2 w-2 rounded-full bg-brand-500" /> {{ items.length }} to review</span>
            <span class="flex items-center gap-1.5 text-brand-700"><span class="h-2 w-2 rounded-full bg-lavender" /> {{ kept }} kept</span>
            <span class="flex items-center gap-1.5 text-ink-400"><span class="h-2 w-2 rounded-full bg-ink-300" /> {{ dismissed }} dismissed</span>
          </div>
        </div>
        <div class="mt-2.5 h-1.5 overflow-hidden rounded-full bg-surface-100">
          <div class="h-full rounded-full bg-gradient-to-r from-brand-600 to-lavender transition-all duration-500" :style="{ width: `${Math.max(progressPct, 3)}%` }" />
        </div>
      </div>

      <div v-if="!items.length" class="dash-card mb-5 px-4 py-8 text-center">
        <p class="text-[14px] font-semibold text-ink-800">All caught up 🎉</p>
        <p class="mt-1 text-[12px] text-ink-400">You reviewed every suggestion from this visit. New ones appear as your records grow.</p>
      </div>

      <div class="space-y-5">
        <section v-for="[type, group] in grouped" :key="type">
          <div class="mb-2.5 flex items-center gap-2.5">
            <span class="dash-icon-tile h-9 w-9" :class="meta(type).tone">
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

          <!-- One full-width card per row everywhere -->
          <div class="grid gap-3">
            <article
              v-for="item in group"
              :key="item.id"
              class="dash-card flex flex-col p-4"
              :class="priority(item) === 'FOCUS' ? 'border-terracotta/40' : ''"
            >
              <div class="flex items-start justify-between gap-3">
                <h3 class="text-[14px] font-bold leading-snug text-ink-900">{{ item.title }}</h3>
                <span
                  v-if="priority(item)"
                  class="chip shrink-0 font-semibold"
                  :class="priority(item) === 'FOCUS' ? 'bg-terracotta-light text-terracotta-dark' : 'bg-brand-50 text-brand-700'"
                >
                  <span class="h-1.5 w-1.5 rounded-full" :class="priority(item) === 'FOCUS' ? 'bg-terracotta' : 'bg-brand-500'" />
                  {{ priority(item) === 'FOCUS' ? 'Flagged' : 'Action' }}
                </span>
                <span v-else class="chip shrink-0" :class="meta(type).tone">{{ meta(type).title.split(' ')[0] }}</span>
              </div>
              <p class="mt-1.5 flex-1 text-[13px] leading-relaxed text-ink-600">{{ item.body }}</p>

              <p class="mt-2.5 flex items-start gap-1.5 border-t border-ink-100 pt-2.5 text-[11px] leading-relaxed text-ink-400">
                <svg class="mt-0.5 h-3 w-3 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M12 8v5m0 3v.5M12 3a9 9 0 100 18 9 9 0 000-18z" stroke-linecap="round" />
                </svg>
                {{ basisText(item) || footerNote(item.type) }}
              </p>

              <div class="mt-3 flex flex-wrap items-center gap-2">
                <RouterLink v-if="actionFor(item)" :to="actionFor(item)!.to" class="dash-btn px-3 py-1.5 text-xs">
                  {{ actionFor(item)!.label }} →
                </RouterLink>
                <button
                  class="btn-secondary px-3 py-1.5 text-xs"
                  :disabled="busy === item.id"
                  @click="respond(item, 'ACCEPTED')"
                >Keep</button>
                <button
                  class="btn-ghost px-2.5 py-1.5 text-xs"
                  :disabled="busy === item.id"
                  @click="respond(item, 'DISMISSED')"
                >Dismiss</button>
                <button
                  class="ml-auto rounded-lg px-2 py-1.5 text-[11px] font-semibold text-ink-400 transition-colors hover:bg-surface-100 hover:text-brand-700"
                  @click="copyItem(item)"
                >{{ copiedId === item.id ? '✓ Copied' : 'Copy' }}</button>
              </div>
            </article>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>
