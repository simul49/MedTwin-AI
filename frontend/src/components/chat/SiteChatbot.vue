<script setup lang="ts">
import { nextTick, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { ai } from '@/api/endpoints';

const { t, locale } = useI18n();

interface WidgetMessage {
  role: 'user' | 'ai';
  text: string;
  sources?: { ref: number; title: string; sourceTitle: string; url: string }[];
}

const open = ref(false);
const sending = ref(false);
const draft = ref('');
const listEl = ref<HTMLElement | null>(null);
const messages = ref<WidgetMessage[]>([]);

function toggle() {
  open.value = !open.value;
  if (open.value && messages.value.length === 0) {
    messages.value.push({ role: 'ai', text: t('chatbot.welcome') });
  }
  if (open.value) scrollDown();
}

async function scrollDown() {
  await nextTick();
  if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight;
}

async function send() {
  const text = draft.value.trim();
  if (!text || sending.value) return;
  draft.value = '';
  messages.value.push({ role: 'user', text });
  sending.value = true;
  scrollDown();
  try {
    const reply = await ai.publicChat(text.slice(0, 1000), locale.value);
    messages.value.push({ role: 'ai', text: reply.answer, sources: reply.sources });
  } catch {
    messages.value.push({ role: 'ai', text: t('chatbot.error') });
  } finally {
    sending.value = false;
    scrollDown();
  }
}
</script>

<template>
  <div class="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
    <Transition name="pop">
      <section
        v-if="open"
        class="flex max-h-[min(600px,calc(100vh-120px))] w-[min(380px,calc(100vw-40px))] flex-col overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-lift"
        aria-label="MedTwin website chatbot"
      >
        <header class="flex items-center justify-between border-b border-ink-200 bg-white px-4 py-3">
          <div>
            <p class="text-sm font-bold text-ink-900">{{ t('chatbot.title') }}</p>
            <p class="text-[11px] text-ink-500">{{ t('chatbot.subtitle') }}</p>
          </div>
          <button class="rounded-lg p-1.5 text-ink-400 transition-colors hover:bg-ink-100 hover:text-ink-700" @click="open = false">
            <span class="sr-only">Close</span>
            <svg viewBox="0 0 20 20" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 5l10 10M15 5L5 15" stroke-linecap="round" />
            </svg>
          </button>
        </header>

        <div ref="listEl" class="dash-scroll flex-1 space-y-3 overflow-y-auto bg-surface-50 px-4 py-4">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="flex"
            :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div
              class="max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed"
              :class="msg.role === 'user'
                ? 'rounded-br-sm bg-brand-600 text-white'
                : 'rounded-bl-sm border border-ink-200 bg-white text-ink-800'"
            >
              {{ msg.text }}
              <div v-if="msg.sources && msg.sources.length" class="mt-2 flex flex-wrap gap-1.5">
                <a
                  v-for="source in msg.sources"
                  :key="source.ref"
                  :href="source.url || '#'"
                  target="_blank"
                  rel="noopener"
                  class="rounded-full border border-brand-200 bg-brand-50 px-2 py-0.5 text-[10px] font-semibold text-brand-700 hover:underline"
                >
                  [{{ source.ref }}] {{ source.title || source.sourceTitle }}
                </a>
              </div>
            </div>
          </div>

          <div v-if="sending" class="flex justify-start">
            <div class="rounded-2xl rounded-bl-sm border border-ink-200 bg-white px-3.5 py-2.5 text-sm text-ink-400">
              {{ t('chatbot.thinking') }}
            </div>
          </div>
        </div>

        <p class="border-t border-ink-200 bg-white px-4 py-2 text-[10px] leading-snug text-ink-400">
          {{ t('chatbot.disclaimer') }}
        </p>

        <form class="flex items-center gap-2 border-t border-ink-200 bg-white px-3 py-3" @submit.prevent="send">
          <input
            v-model="draft"
            class="input h-9 flex-1 text-sm"
            :placeholder="t('chatbot.placeholder')"
            maxlength="1000"
          />
          <button class="btn-primary h-9 w-9 justify-center p-0" type="submit" :disabled="sending || !draft.trim()">
            <svg viewBox="0 0 20 20" class="h-4 w-4" fill="currentColor">
              <path d="M3 10l13-7-4.2 7L16 17 3 10zm0 0h7" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linejoin="round" />
            </svg>
          </button>
        </form>
      </section>
    </Transition>

    <button
      class="flex h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-white shadow-lift transition-transform hover:scale-105 active:scale-95"
      aria-label="Open chat"
      @click="toggle"
    >
      <svg v-if="!open" viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8z" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <svg v-else viewBox="0 0 20 20" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M5 5l10 10M15 5L5 15" stroke-linecap="round" />
      </svg>
    </button>
  </div>
</template>
