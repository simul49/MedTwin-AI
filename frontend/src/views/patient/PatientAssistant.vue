<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ai } from '@/api/endpoints';
import type { ChatResponse } from '@/api/types';

interface Turn {
  id: string;
  role: 'user' | 'ai';
  body: string;           // currently displayed text (typewriter)
  full?: string;          // final text
  result?: ChatResponse;
  showSources?: boolean;
}

const turns = ref<Turn[]>([]);
const draft = ref('');
const sending = ref(false);
const error = ref<string | null>(null);
const scroller = ref<HTMLElement | null>(null);
const textareaEl = ref<HTMLTextAreaElement | null>(null);
const activeConversation = ref<string | null>(null);
let typewriter: ReturnType<typeof setInterval> | null = null;

const SUGGESTIONS = [
  'What do my BP readings mean?',
  'Explain my HbA1c result',
  'Is my heart rate normal?',
  'My health trends this month',
  'Records needing verification?',
  'Questions for my doctor?',
  'Tips for better sleep & energy',
  'My medications in simple terms',
];
const suggestions = ref<string[]>([...SUGGESTIONS]);

const latest = computed(() => [...turns.value].reverse().find((turn) => turn.result)?.result ?? null);
const providerLabel = computed(() => {
  const mode = latest.value?.model?.generationMode;
  if (!mode) return null;
  return mode === 'provider' ? 'Live model · source-grounded' : 'Built-in composer · source-grounded';
});
const trustLabel = computed(() => {
  if (!latest.value) return 'NOT RATED';
  const score = latest.value.safety.score;
  return score >= 85 ? 'HIGH' : score >= 60 ? 'MODERATE' : 'LOW';
});

const factorNames: Record<string, string> = {
  source_grounding: 'Grounding',
  reference_availability: 'Reference availability',
  context_match: 'Context match',
  contradiction_check: 'Contradiction check',
  unsupported_claims: 'Unsupported claims check',
  safety_rules: 'Safety rules',
  risk_routing: 'Risk routing',
};

/** Minimal, escape-first markdown: **bold**, `code`, "- " bullets, paragraphs. */
function renderMarkdown(raw: string): string {
  const escaped = raw.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const inline = (s: string) =>
    s.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-ink-900">$1</strong>')
      .replace(/`(.+?)`/g, '<code class="rounded bg-ink-100 px-1 py-0.5 text-[12px]">$1</code>');
  const out: string[] = [];
  let inList = false;
  for (const line of escaped.split('\n')) {
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    if (bullet) {
      if (!inList) {
        out.push('<ul class="ml-4 list-disc space-y-1">');
        inList = true;
      }
      out.push(`<li>${inline(bullet[1])}</li>`);
    } else if (line.trim()) {
      if (inList) {
        out.push('</ul>');
        inList = false;
      }
      out.push(`<p>${inline(line)}</p>`);
    }
  }
  if (inList) out.push('</ul>');
  return out.join('');
}

async function scroll() {
  await nextTick();
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: 'smooth' });
}

function autoGrow() {
  const el = textareaEl.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
}

function reveal(full: string, turn: Turn, done: () => void) {
  const chunk = Math.max(2, Math.ceil(full.length / 90));
  typewriter = setInterval(() => {
    turn.body = full.slice(0, turn.body.length + chunk);
    scroll();
    if (turn.body.length >= full.length) {
      turn.body = full;
      if (typewriter) clearInterval(typewriter);
      typewriter = null;
      done();
    }
  }, 16);
}

function newConversation() {
  turns.value = [];
  activeConversation.value = null;
  suggestions.value = [...SUGGESTIONS];
  error.value = null;
}

async function send(message?: string) {
  const text = (message ?? draft.value).trim();
  if (!text || sending.value) return;

  suggestions.value = [];
  turns.value.push({ id: `u-${Date.now()}`, role: 'user', body: text });
  draft.value = '';
  autoGrow();
  sending.value = true;
  error.value = null;
  await scroll();

  try {
    const result = await ai.chat(text, activeConversation.value ?? undefined);
    const turn: Turn = { id: result.interactionId, role: 'ai', body: '', full: result.answer, result };
    // Keep the reactive proxy so typewriter mutations trigger re-renders.
    const reactiveTurn = turns.value[turns.value.push(turn) - 1];
    activeConversation.value = null;
    reveal(result.answer, reactiveTurn, () => scroll());
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    sending.value = false;
    await scroll();
  }
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    send();
  }
}

// Pre-fill the composer when arriving from another page (e.g. a recommendation card).
const route = useRoute();
const router = useRouter();
onMounted(() => {
  const prefill = typeof route.query.q === 'string' ? route.query.q.trim() : '';
  if (prefill) {
    draft.value = prefill;
    nextTick(() => textareaEl.value?.focus());
    router.replace({ query: { ...route.query, q: undefined } });
  }
});

onBeforeUnmount(() => {
  if (typewriter) clearInterval(typewriter);
});
</script>

<template>
  <div>
    <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-700 to-lavender text-white shadow-lift">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M12 3l1.9 4.6L18.5 9l-4.6 1.9L12 15.5l-1.9-4.6L5.5 9l4.6-1.4L12 3z" stroke-linejoin="round" />
          </svg>
        </div>
        <div>
          <h1 class="text-[24px] font-bold leading-tight tracking-tight text-ink-900">AI Health Assistant</h1>
          <p class="mt-0.5 flex items-center gap-1.5 text-[12px] text-ink-500">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Grounded in your records and approved sources
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="providerLabel" class="chip border border-brand-200 bg-brand-50 px-3 py-1.5 text-brand-700">{{ providerLabel }}</span>
        <button class="btn-secondary text-xs" @click="newConversation">＋ New conversation</button>
      </div>
    </div>

    <div class="space-y-4">
        <div class="dash-card flex h-[min(640px,calc(100vh-260px))] flex-col overflow-hidden">
          <!-- Chat body -->
          <div ref="scroller" class="dash-scroll flex-1 space-y-4 overflow-y-auto bg-surface-50/60 px-5 py-5">
            <!-- Welcome -->
            <div v-if="!turns.length" class="flex h-full flex-col items-center justify-center py-6 text-center">
              <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-700 to-lavender text-white shadow-lift">
                <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                  <path d="M4 5h16v11H9l-5 4zM8 10h8M8 13h5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </div>
              <p class="mt-4 text-[16px] font-bold text-ink-900">Ask about your health information</p>
              <p class="mt-1.5 max-w-sm text-[12.5px] leading-relaxed text-ink-500">
                Every answer is grounded in your records and approved sources, with a visible trust rating.
              </p>
              <div class="mt-5 grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
                <button
                  v-for="suggestion in suggestions"
                  :key="suggestion"
                  class="group flex items-center justify-between gap-1.5 rounded-lg border border-ink-200 bg-white px-3 py-2 text-left text-[12px] text-ink-700 transition-all hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card"
                  @click="send(suggestion)"
                >
                  {{ suggestion }}
                  <svg viewBox="0 0 20 20" class="h-3 w-3 shrink-0 text-ink-300 transition-colors group-hover:text-brand-500" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 10h12m0 0l-4-4m4 4l-4 4" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Messages -->
            <template v-for="turn in turns" :key="turn.id">
              <div class="flex gap-3" :class="turn.role === 'user' ? 'justify-end' : 'justify-start'">
                <div
                  v-if="turn.role === 'ai'"
                  class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-700 to-lavender text-white"
                >
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 3l1.9 4.6L18.5 9l-4.6 1.9L12 15.5l-1.9-4.6L5.5 9l4.6-1.4L12 3z" stroke-linejoin="round" />
                  </svg>
                </div>

                <div class="max-w-[84%]" :class="turn.role === 'user' ? 'items-end' : 'items-start'">
                  <div
                    class="rounded-2xl px-4 py-3 text-[13.5px] leading-relaxed shadow-sm"
                    :class="turn.role === 'user'
                      ? 'rounded-br-md bg-gradient-to-br from-brand-600 to-brand-700 text-white'
                      : 'rounded-bl-md border border-ink-200 bg-white text-ink-800'"
                  >
                    <template v-if="turn.role === 'user'">{{ turn.body }}</template>
                    <template v-else><span v-html="renderMarkdown(turn.body)" /></template>
                    <span
                      v-if="turn.role === 'ai' && turn.body.length < (turn.full ?? '').length"
                      class="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse rounded-sm bg-brand-500 align-middle"
                    />
                  </div>

                  <!-- Trust + sources row -->
                  <div v-if="turn.role === 'ai' && turn.result && turn.body.length >= (turn.full ?? '').length" class="mt-2 flex flex-wrap items-center gap-2">
                    <span
                      class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10.5px] font-semibold"
                      :class="turn.result.safety.score >= 85 ? 'bg-brand-50 text-brand-700' : turn.result.safety.score >= 60 ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'"
                    >
                      <svg viewBox="0 0 20 20" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 2l7 2.5V10c0 4-3 6.5-7 7.5C6 16.5 3 14 3 10V4.5z" stroke-linejoin="round" />
                      </svg>
                      Trust {{ turn.result.safety.score.toFixed(0) }}/100
                    </span>
                    <button
                      v-if="turn.result.sources.length"
                      class="inline-flex items-center gap-1.5 rounded-full border border-ink-200 bg-white px-2.5 py-1 text-[10.5px] font-medium text-ink-500 transition-colors hover:border-brand-300 hover:text-brand-700"
                      @click="turn.showSources = !turn.showSources"
                    >
                      {{ turn.result.sources.length }} source{{ turn.result.sources.length > 1 ? 's' : '' }}
                      <svg viewBox="0 0 20 20" class="h-2.5 w-2.5 transition-transform" :class="turn.showSources ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M5 8l5 5 5-5" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </button>
                  </div>
                  <div v-if="turn.showSources" class="mt-2 space-y-1.5 rounded-xl border border-ink-200 bg-white p-2.5">
                    <a
                      v-for="source in turn.result?.sources ?? []"
                      :key="source.chunkId"
                      :href="source.url || '#'"
                      target="_blank"
                      rel="noopener"
                      class="flex items-start gap-2 rounded-lg px-2 py-1 text-[11.5px] text-ink-600 hover:bg-brand-50 hover:text-brand-700"
                    >
                      <span class="flex h-4 w-4 shrink-0 items-center justify-center rounded bg-brand-50 text-[9px] font-bold text-brand-700">{{ source.ref }}</span>
                      <span class="leading-snug">
                        {{ source.sourceTitle }}
                        <span v-if="source.publisher" class="text-ink-400"> — {{ source.publisher }}</span>
                      </span>
                    </a>
                  </div>
                </div>
              </div>
            </template>

            <!-- Thinking indicator -->
            <div v-if="sending" class="flex gap-3">
              <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-700 to-lavender text-white">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 3l1.9 4.6L18.5 9l-4.6 1.9L12 15.5l-1.9-4.6L5.5 9l4.6-1.4L12 3z" stroke-linejoin="round" />
                </svg>
              </div>
              <div class="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-ink-200 bg-white px-4 py-3.5">
                <span class="typing-dot" />
                <span class="typing-dot" style="animation-delay: 0.15s" />
                <span class="typing-dot" style="animation-delay: 0.3s" />
                <span class="ml-1.5 text-[11px] text-ink-400">Checking your records and approved sources…</span>
              </div>
            </div>
          </div>

          <!-- Composer -->
          <div class="border-t border-ink-100 bg-white p-3">
            <p v-if="error" class="mb-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-[11px] text-rose-700">{{ error }}</p>
            <div class="flex items-end gap-2">
              <textarea
                ref="textareaEl"
                v-model="draft"
                rows="1"
                class="input max-h-[120px] min-h-[42px] flex-1 resize-none py-2.5 text-sm"
                placeholder="Ask about your health information…"
                @input="autoGrow"
                @keydown="onKeydown"
              />
              <button
                class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white transition-all hover:bg-brand-700 active:scale-95 disabled:opacity-40"
                :disabled="sending || !draft.trim()"
                @click="send()"
              >
                <svg viewBox="0 0 20 20" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 10l14-7-5.5 7L17 17 3 10zm0 0h7" stroke-linejoin="round" />
                </svg>
              </button>
            </div>
            <p class="mt-1.5 text-[10px] text-ink-400">Enter to send · Shift+Enter for a new line</p>
          </div>
        </div>

        <!-- Safety panel -->
        <div v-if="latest" class="dash-card dash-card-pad">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="flex items-start gap-3">
              <span class="dash-icon-tile">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="dash-section-title">Trust Rating: {{ trustLabel }}</p>
                <p class="dash-section-sub mt-0.5">Automated safety checks on the latest answer</p>
              </div>
            </div>
            <span
              class="chip"
              :class="trustLabel === 'HIGH' ? 'bg-brand-50 text-brand-700' : trustLabel === 'NOT RATED' ? 'bg-surface-100 text-ink-500' : 'bg-amber-50 text-amber-700'"
            >
              {{ latest.safety.score.toFixed(0) }}/100
            </span>
          </div>
          <div class="mt-4">
            <div class="h-1.5 w-full overflow-hidden rounded-full bg-ink-100">
              <div class="h-full rounded-full bg-brand-500 transition-all duration-700" :style="{ width: `${latest.safety.score}%` }" />
            </div>
            <div class="mt-4 grid grid-cols-2 gap-x-3 gap-y-2.5 sm:grid-cols-3 lg:grid-cols-4">
              <div
                v-for="factor in latest.safety.factors"
                :key="factor.key"
                class="flex items-center gap-2 text-[11px] text-ink-600"
              >
                <span
                  class="h-1.5 w-1.5 shrink-0 rounded-full"
                  :class="factor.status === 'pass' ? 'bg-brand-500' : factor.status === 'warn' ? 'bg-amber-500' : 'bg-rose-400'"
                />
                {{ factorNames[factor.key] ?? factor.label }}
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3.5">
          <svg class="mt-0.5 h-4 w-4 shrink-0 text-amber-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M12 3l10 18H2zM12 9v5M12 17h.01" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <p class="text-[12px] leading-relaxed text-amber-900">
            This is educational information only — not medical advice. Always consult a healthcare provider.
          </p>
        </div>
      </div>
    </div>
</template>

<style scoped>
.typing-dot {
  height: 6px;
  width: 6px;
  border-radius: 9999px;
  background: var(--color-brand-500, #16a34a);
  animation: typing-bounce 1s ease-in-out infinite;
}
@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}
</style>
