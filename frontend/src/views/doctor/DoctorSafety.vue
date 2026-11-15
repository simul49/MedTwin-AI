<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { ai } from '@/api/endpoints';
import type { Safety } from '@/api/types';
import SafetyPanel from '@/components/ui/SafetyPanel.vue';

const { t } = useI18n();

const draft = ref('');
const result = ref<Safety | null>(null);
const evaluating = ref(false);
const error = ref<string | null>(null);

const MAX_CHARS = 4000;

const charCount = computed(() => `${draft.value.length} / ${MAX_CHARS}`);

const SAMPLE = `Your recent readings show systolic pressure around 132 mmHg, which is slightly above the normal range (below 120 mmHg) [1]. This can be influenced by stress, sleep quality and salt intake.

If it stays elevated across several readings, please discuss it with your clinician — you can review your medication plan and lifestyle habits together. This is educational information, not medical advice.`;

const VERDICT: Record<string, { chip: string; label: string }> = {
  PASS: { chip: 'bg-emerald-50 text-emerald-700', label: 'Safe to send' },
  REVIEW: { chip: 'bg-amber-50 text-amber-700', label: 'Review before sending' },
  BLOCK: { chip: 'bg-rose-50 text-rose-700', label: 'Do not send as drafted' },
};

const verdict = computed(() => {
  if (!result.value) return null;
  if (result.value.score >= 80) return VERDICT.PASS;
  if (result.value.score >= 55) return VERDICT.REVIEW;
  return VERDICT.BLOCK;
});

function insertSample() {
  draft.value = SAMPLE;
}

async function evaluate() {
  if (!draft.value.trim() || evaluating.value) return;
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
    <div class="mb-6">
      <p class="dash-kicker mb-2">Trust &amp; safety</p>
      <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">Evaluate a draft answer</h1>
      <p class="mt-2 max-w-2xl text-[14px] text-ink-500">
        Paste any AI-drafted reply before you send it to a patient. The evaluator runs the same
        automated checks used across the platform — grounding, contradiction detection and safety
        policies — and returns a trust score.
      </p>
    </div>

    <div class="grid items-start gap-6 lg:grid-cols-2">
      <!-- Draft input -->
      <div class="dash-card dash-card-pad">
        <div class="mb-3 flex items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <span class="dash-icon-tile bg-brand-50 text-brand-700" aria-hidden="true">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <path d="M4 6h16M4 12h10M4 18h7" stroke-linecap="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Draft answer</p>
              <p class="dash-section-sub mt-0.5">Paste or type the reply you plan to send</p>
            </div>
          </div>
          <button class="btn-ghost text-xs" @click="insertSample">Insert example</button>
        </div>

        <textarea
          v-model="draft"
          class="input min-h-48 resize-y font-sans leading-relaxed"
          :maxlength="MAX_CHARS"
          placeholder="Paste the draft answer here — for example, a reply you are preparing in Messages or a suggestion drafted by the AI assistant…"
        />
        <p class="mt-1 text-right text-[11px] text-ink-400">{{ charCount }}</p>

        <button
          class="dash-btn mt-3 w-full"
          :disabled="evaluating || !draft.trim()"
          @click="evaluate"
        >
          {{ evaluating ? 'Evaluating…' : 'Run safety evaluation' }}
        </button>
        <p v-if="error" class="mt-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-[13px] text-rose-700">
          {{ error }}
        </p>
        <p class="mt-3 text-[11px] leading-snug text-ink-400">
          The trust score is an evaluation aid — it is not a guarantee of medical correctness, and a
          high value never bypasses safety rules.
        </p>
      </div>

      <!-- Result -->
      <div class="space-y-4">
        <template v-if="result">
          <div class="flex items-center justify-between gap-3 rounded-2xl border border-ink-200 bg-white px-5 py-4">
            <div class="flex items-center gap-3">
              <span
                class="dash-icon-tile"
                :class="verdict === VERDICT.PASS ? 'bg-emerald-50 text-emerald-700' : verdict === VERDICT.REVIEW ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'"
                aria-hidden="true"
              >
                <svg v-if="verdict === VERDICT.PASS" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                  <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                  <path d="M12 9v4m0 4h.01M12 3l9 16H3z" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="dash-section-title">Evaluation result</p>
                <p class="dash-section-sub mt-0.5">Seven automated checks · trust score {{ result.score }}/100</p>
              </div>
            </div>
            <span class="chip" :class="verdict?.chip">{{ verdict?.label }}</span>
          </div>
          <SafetyPanel :safety="result" />
        </template>

        <!-- Empty state before first evaluation -->
        <div v-else class="dash-card dash-card-pad">
          <div class="flex items-center gap-3">
            <span class="dash-icon-tile" aria-hidden="true">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <path d="M12 3l8 3v6c0 4.5-3.2 7.6-8 9-4.8-1.4-8-4.5-8-9V6z" />
                <path d="M9 12l2 2 4-4" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">No evaluation yet</p>
              <p class="dash-section-sub mt-0.5">Run an evaluation to see the trust report here</p>
            </div>
          </div>
          <ul class="mt-4 space-y-2 text-[13px] text-ink-600">
            <li class="flex items-start gap-2">
              <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
              A trust score from 0–100 with a clear pass / review / block verdict
            </li>
            <li class="flex items-start gap-2">
              <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
              Seven checks: source grounding, reference availability, context match,
              contradiction check, safety rules, unsupported claims and risk routing
            </li>
            <li class="flex items-start gap-2">
              <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
              Per-check pass / warn / fail detail, so you can fix the weak spots before sending
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
