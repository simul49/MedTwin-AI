<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { ai } from '@/api/endpoints';
import type { ChatResponse } from '@/api/types';

interface Turn {
  id: string;
  role: 'user' | 'ai';
  body: string;
  result?: ChatResponse;
}

interface ConversationItem {
  id: string;
  title: string;
  updatedAt: string | null;
  messageCount: number;
}

const turns = ref<Turn[]>([]);
const draft = ref('');
const sending = ref(false);
const error = ref<string | null>(null);
const scroller = ref<HTMLElement | null>(null);
const conversations = ref<ConversationItem[]>([]);
const activeConversation = ref<string | null>(null);

const SUGGESTIONS = [
  'What do my recent blood pressure readings mean?',
  'Explain my HbA1c result',
  'How should I prepare for my next appointment?',
];

const latest = computed(() => [...turns.value].reverse().find((turn) => turn.result)?.result ?? null);
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

async function scroll() {
  await nextTick();
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: 'smooth' });
}

async function loadConversations() {
  try {
    conversations.value = (await ai.conversations()).results;
  } catch {
    conversations.value = [];
  }
}

async function openConversation(id: string) {
  try {
    const detail = await ai.conversation(id);
    activeConversation.value = id;
    turns.value = detail.messages.map((m) => ({
      id: m.id,
      role: m.role === 'USER' ? 'user' : 'ai',
      body: m.body,
    }));
    await scroll();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
}

function newConversation() {
  turns.value = [];
  activeConversation.value = null;
  error.value = null;
}

async function send(message?: string, conversationId?: string) {
  const text = (message ?? draft.value).trim();
  if (!text || sending.value) return;

  turns.value.push({ id: `u-${Date.now()}`, role: 'user', body: text });
  draft.value = '';
  sending.value = true;
  error.value = null;
  await scroll();

  try {
    const result = await ai.chat(text, conversationId ?? activeConversation.value ?? undefined);
    turns.value.push({ id: result.interactionId, role: 'ai', body: result.answer, result });
    activeConversation.value = null;
    await loadConversations();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    sending.value = false;
    await scroll();
  }
}

onMounted(loadConversations);
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Grounded AI</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">AI Health Assistant</h1>
        <p class="mt-2 text-[14px] text-ink-500">Grounded answers with visible sources and a trust rating.</p>
      </div>
      <span class="chip border border-brand-200 bg-brand-50 px-3 py-1.5 text-brand-700">Offline composer · source-grounded</span>
    </div>

    <div class="grid gap-4 xl:grid-cols-[260px_minmax(0,1fr)]">
      <!-- Conversation rail -->
      <aside class="dash-card hidden max-h-[420px] flex-col self-start xl:flex">
        <div class="flex items-start gap-3 border-b border-ink-100 px-4 py-4">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M4 5h16v11H9l-5 4z" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div>
            <p class="dash-section-title">Conversations</p>
            <p class="dash-section-sub mt-0.5">Recent health questions</p>
          </div>
        </div>
        <div class="dash-scroll flex-1 space-y-1 overflow-y-auto p-2">
          <button
            v-for="(item, index) in conversations"
            :key="item.id"
            class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-brand-50"
            :class="activeConversation === item.id ? 'bg-brand-50' : ''"
            @click="openConversation(item.id)"
          >
            <span
              class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
              :class="index % 3 === 0 ? 'bg-brand-500' : index % 3 === 1 ? 'bg-amber-500' : 'bg-sky-500'"
            >
              {{ index + 1 }}
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-[12px] font-medium text-ink-700">{{ item.title || 'Health question' }}</span>
              <span class="block text-[10px] text-ink-400">{{ item.messageCount }} messages</span>
            </span>
          </button>
          <p v-if="!conversations.length" class="px-3 py-4 text-[12px] text-ink-400">No saved conversations yet.</p>
        </div>
      </aside>

      <!-- Chat + evidence -->
      <div class="min-w-0 space-y-4">
        <div class="dash-card flex h-[330px] flex-col overflow-hidden">
          <div class="flex items-center justify-between border-b border-ink-100 px-4 py-2.5">
            <p class="text-[12px] font-semibold text-ink-700">Conversation</p>
            <button class="text-[11px] font-semibold text-brand-700 hover:underline" @click="newConversation">＋ New</button>
          </div>

          <div ref="scroller" class="dash-scroll flex-1 space-y-4 overflow-y-auto bg-surface-50/60 p-4">
            <div v-if="!turns.length" class="flex h-full flex-col items-center justify-center py-8 text-center">
              <span class="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50">
                <svg class="h-6 w-6 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                  <path d="M4 5h16v11H9l-5 4zM8 10h8M8 13h5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <p class="mt-4 text-[14px] font-bold text-ink-800">Ask about your health information</p>
              <p class="mt-1 max-w-sm text-[12px] leading-relaxed text-ink-500">
                Every answer is grounded in your records and approved sources, with a visible trust rating.
              </p>
            </div>

            <div v-for="turn in turns" :key="turn.id" class="flex" :class="turn.role === 'ai' ? 'justify-end' : 'justify-start'">
              <div
                class="max-w-[86%] rounded-2xl px-4 py-3 text-[13px] leading-relaxed shadow-sm"
                :class="turn.role === 'ai'
                  ? 'rounded-br-sm bg-brand-600 text-white'
                  : 'rounded-bl-sm border border-ink-200 bg-white text-ink-800'"
              >
                <p class="whitespace-pre-wrap">{{ turn.body }}</p>
              </div>
            </div>

            <p v-if="sending" class="text-[12px] text-ink-400">Composing a grounded answer…</p>
          </div>

          <div class="border-t border-ink-100 p-3">
            <div class="mb-2 flex flex-wrap gap-1.5">
              <button
                v-for="suggestion in SUGGESTIONS"
                :key="suggestion"
                class="rounded-full border border-ink-200 px-2.5 py-1 text-[11px] text-ink-600 transition-colors hover:border-brand-300 hover:text-brand-700"
                @click="send(suggestion)"
              >
                {{ suggestion }}
              </button>
            </div>
            <form class="flex gap-2" @submit.prevent="send()">
              <input v-model="draft" class="input" placeholder="Ask about your health information…" />
              <button class="dash-btn shrink-0" type="submit" :disabled="sending">Send</button>
            </form>
            <p v-if="error" class="mt-2 text-[11px] text-rose-600">{{ error }}</p>
          </div>
        </div>

        <!-- Evidence cards (only once there is an answer to explain) -->
        <div v-if="latest" class="grid gap-4 lg:grid-cols-2">
          <div class="dash-card dash-card-pad">
            <div class="flex items-start gap-3">
              <span class="dash-icon-tile">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path d="M4 4h7v16H4zM13 4h7v16h-7zM6.5 8h2M15.5 8h2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <div>
                <p class="dash-section-title">Source References</p>
                <p class="dash-section-sub mt-0.5">Approved passages used for this answer</p>
              </div>
            </div>
            <ul v-if="latest?.sources.length" class="mt-4 space-y-2.5">
              <li v-for="source in latest.sources" :key="source.chunkId" class="flex items-start gap-2.5 text-[12px] text-ink-700">
                <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-brand-50 text-[10px] font-bold text-brand-700">
                  {{ source.ref }}
                </span>
                <span class="leading-relaxed">
                  <a v-if="source.url" :href="source.url" target="_blank" rel="noopener" class="font-medium hover:underline">
                    {{ source.sourceTitle }}
                  </a>
                  <span v-else class="font-medium">{{ source.sourceTitle }}</span>
                  <span v-if="source.publisher" class="text-ink-400"> — {{ source.publisher }}</span>
                </span>
              </li>
            </ul>
            <p v-else class="mt-4 text-[12px] text-ink-400">Sources appear after you ask a question.</p>
          </div>

          <div class="dash-card dash-card-pad">
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-start gap-3">
                <span class="dash-icon-tile">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path d="M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </span>
                <div>
                  <p class="dash-section-title">Trust Rating: {{ trustLabel }}</p>
                  <p class="dash-section-sub mt-0.5">Automated safety checks</p>
                </div>
              </div>
              <span
                class="chip"
                :class="trustLabel === 'HIGH' ? 'bg-brand-50 text-brand-700' : trustLabel === 'NOT RATED' ? 'bg-surface-100 text-ink-500' : 'bg-amber-50 text-amber-700'"
              >
                {{ latest ? `${latest.safety.score.toFixed(0)}/100` : '—' }}
              </span>
            </div>
            <div v-if="latest" class="mt-4">
              <div class="h-1.5 w-full overflow-hidden rounded-full bg-ink-100">
                <div class="h-full rounded-full bg-brand-500 transition-all duration-700" :style="{ width: `${latest.safety.score}%` }" />
              </div>
              <div class="mt-4 grid grid-cols-2 gap-x-3 gap-y-2.5">
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
            <p v-else class="mt-4 text-[12px] text-ink-400">Automated checks appear with each answer.</p>
          </div>
        </div>

        <div v-else class="dash-card flex flex-wrap items-center gap-4 px-5 py-4">
          <span class="dash-icon-tile">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div class="min-w-[200px] flex-1">
            <p class="dash-section-title">Every answer is checked before you see it</p>
            <p class="dash-section-sub mt-0.5">Grounding, reference availability, contradiction and unsupported-claim checks run automatically. Sources and a trust score appear with each answer.</p>
          </div>
          <span class="chip bg-brand-50 text-brand-700">7 safety factors</span>
        </div>

        <div class="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3.5">
          <svg class="mt-0.5 h-4 w-4 shrink-0 text-amber-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M12 3l10 18H2zM12 9v5M12 17h.01" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <p class="text-[12px] leading-relaxed text-amber-900">
            This is educational information only — not medical advice. Always consult a healthcare provider.
          </p>
        </div>

        <div v-if="turns.length" class="flex justify-end">
          <button class="dash-btn" @click="newConversation">Start new conversation</button>
        </div>
      </div>
    </div>
  </div>
</template>
