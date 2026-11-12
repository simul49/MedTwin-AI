<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { ai } from '@/api/endpoints';

const { t, locale } = useI18n();

interface WidgetSource {
  ref: number;
  title: string;
  sourceTitle: string;
  url: string;
}

interface WidgetMessage {
  role: 'user' | 'ai';
  text: string;          // currently displayed text (typewriter)
  full?: string;         // final text (user messages render text directly)
  sources?: WidgetSource[];
  showSources?: boolean;
}

const open = ref(false);
const sending = ref(false);
const draft = ref('');
const listEl = ref<HTMLElement | null>(null);
const messages = ref<WidgetMessage[]>([]);
const textareaEl = ref<HTMLTextAreaElement | null>(null);
let typewriter: ReturnType<typeof setInterval> | null = null;

const suggestions = ref<string[]>([]);

function refillSuggestions() {
  suggestions.value = [t('chatbot.s1'), t('chatbot.s2'), t('chatbot.s3'), t('chatbot.s4')];
}

function toggle() {
  open.value = !open.value;
  if (open.value && messages.value.length === 0) {
    refillSuggestions();
    messages.value.push({ role: 'ai', text: t('chatbot.welcome'), full: t('chatbot.welcome') });
  }
  if (open.value) {
    scrollDown();
    setTimeout(() => textareaEl.value?.focus(), 150);
  }
}

function scrollDown() {
  nextTick(() => {
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight;
  });
}

function autoGrow() {
  const el = textareaEl.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${Math.min(el.scrollHeight, 110)}px`;
}

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

function reveal(full: string, message: WidgetMessage, done: () => void) {
  const chunk = Math.max(2, Math.ceil(full.length / 80));
  typewriter = setInterval(() => {
    message.text = full.slice(0, message.text.length + chunk);
    scrollDown();
    if (message.text.length >= full.length) {
      message.text = full;
      if (typewriter) clearInterval(typewriter);
      typewriter = null;
      done();
    }
  }, 18);
}

async function ask(rawText: string) {
  const text = rawText.trim();
  if (!text || sending.value) return;
  suggestions.value = [];
  draft.value = '';
  autoGrow();
  messages.value.push({ role: 'user', text });
  sending.value = true;
  scrollDown();
  try {
    const reply = await ai.publicChat(text.slice(0, 1000), locale.value);
    const message: WidgetMessage = { role: 'ai', text: '', full: reply.answer, sources: reply.sources };
    // Keep the reactive proxy so typewriter mutations trigger re-renders.
    const reactiveMessage = messages.value[messages.value.push(message) - 1];
    scrollDown();
    reveal(reply.answer, reactiveMessage, () => {
      sending.value = false;
      scrollDown();
    });
  } catch {
    sending.value = false;
    const last: WidgetMessage = { role: 'ai', text: '', full: t('chatbot.error') };
    const reactiveLast = messages.value[messages.value.push(last) - 1];
    reveal(t('chatbot.error'), reactiveLast, () => scrollDown());
  }
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    ask(draft.value);
  }
}

onBeforeUnmount(() => {
  if (typewriter) clearInterval(typewriter);
});
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="fixed inset-0 z-40 bg-ink-950/20 backdrop-blur-[1px]" @click="open = false" />
    </Transition>

    <div class="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
      <Transition name="pop">
        <section
          v-if="open"
          class="flex h-[min(640px,calc(100vh-96px))] w-[min(420px,calc(100vw-40px))] flex-col overflow-hidden rounded-3xl border border-ink-200 bg-white shadow-lift"
          aria-label="MedTwin website chatbot"
        >
          <!-- Header -->
          <header class="relative bg-gradient-to-r from-brand-900 via-brand-700 to-brand-500 px-4 py-3.5 text-white">
            <div class="flex items-center gap-3">
              <div class="relative flex h-10 w-10 items-center justify-center rounded-2xl bg-white/15 ring-1 ring-white/30 backdrop-blur">
                <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 3l1.9 4.6L18.5 9l-4.6 1.9L12 15.5l-1.9-4.6L5.5 9l4.6-1.4L12 3z" stroke-linejoin="round" />
                  <path d="M19 15l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8.8-2z" stroke-linejoin="round" />
                </svg>
                <span class="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white bg-emerald-400" />
              </div>
              <div class="min-w-0 flex-1">
                <p class="flex items-center gap-2 text-sm font-bold leading-tight">
                  {{ t('chatbot.title') }}
                  <span class="rounded-full bg-white/20 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide">AI</span>
                </p>
                <p class="mt-0.5 text-[11px] text-white/80">{{ t('chatbot.subtitle') }}</p>
              </div>
              <button class="rounded-lg p-1.5 transition-colors hover:bg-white/15" @click="open = false">
                <span class="sr-only">Close</span>
                <svg viewBox="0 0 20 20" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 5l10 10M15 5L5 15" stroke-linecap="round" />
                </svg>
              </button>
            </div>
          </header>

          <!-- Conversation -->
          <div ref="listEl" class="dash-scroll flex-1 space-y-4 overflow-y-auto bg-surface-50 px-4 py-4">
            <!-- Welcome + suggestions -->
            <div v-if="messages.length <= 1 && suggestions.length" class="pt-2">
              <div class="flex flex-col items-center text-center">
                <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-700 to-lavender text-white shadow-lift">
                  <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 3l1.9 4.6L18.5 9l-4.6 1.9L12 15.5l-1.9-4.6L5.5 9l4.6-1.4L12 3z" stroke-linejoin="round" />
                  </svg>
                </div>
                <p class="mt-3 text-base font-bold text-ink-900">{{ t('chatbot.greeting') }}</p>
                <p class="mt-1 text-xs leading-relaxed text-ink-500">{{ t('chatbot.welcomeShort') }}</p>
              </div>
              <div class="mt-4 grid gap-2">
                <button
                  v-for="suggestion in suggestions"
                  :key="suggestion"
                  class="group flex items-center justify-between rounded-xl border border-ink-200 bg-white px-3.5 py-2.5 text-left text-[13px] text-ink-700 transition-all hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card"
                  :disabled="sending"
                  @click="ask(suggestion)"
                >
                  {{ suggestion }}
                  <svg viewBox="0 0 20 20" class="h-3.5 w-3.5 shrink-0 text-ink-300 transition-colors group-hover:text-brand-500" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 10h12m0 0l-4-4m4 4l-4 4" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Messages -->
            <template v-for="(msg, index) in messages" :key="index">
              <div v-if="index > 0 || messages.length > 1" class="flex gap-2.5" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
                <div
                  v-if="msg.role === 'ai'"
                  class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-700 to-lavender text-white"
                >
                  <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 3l1.9 4.6L18.5 9l-4.6 1.9L12 15.5l-1.9-4.6L5.5 9l4.6-1.4L12 3z" stroke-linejoin="round" />
                  </svg>
                </div>

                <div class="max-w-[86%]" :class="msg.role === 'user' ? 'items-end' : 'items-start'">
                  <div
                    class="rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed shadow-sm"
                    :class="msg.role === 'user'
                      ? 'rounded-br-md bg-gradient-to-br from-brand-600 to-brand-700 text-white'
                      : 'rounded-bl-md border border-ink-200 bg-white text-ink-800'"
                  >
                    <template v-if="msg.role === 'user'">{{ msg.text }}</template>
                    <template v-else><span v-html="renderMarkdown(msg.text)" /></template>
                    <span
                      v-if="msg.role === 'ai' && msg.text.length < (msg.full ?? '').length"
                      class="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse rounded-sm bg-brand-500 align-middle"
                    />
                  </div>

                  <!-- Sources -->
                  <div v-if="msg.role === 'ai' && msg.sources && msg.sources.length && msg.text.length >= (msg.full ?? '').length" class="mt-1.5">
                    <button
                      class="flex items-center gap-1.5 rounded-full border border-ink-200 bg-white px-2.5 py-1 text-[11px] font-medium text-ink-500 transition-colors hover:border-brand-300 hover:text-brand-700"
                      @click="msg.showSources = !msg.showSources"
                    >
                      <svg viewBox="0 0 20 20" class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="1.8">
                        <path d="M4 4h8l4 4v8H4V4zm8 0v4h4" stroke-linejoin="round" />
                      </svg>
                      {{ t('chatbot.sources', msg.sources.length) }}
                      <svg viewBox="0 0 20 20" class="h-2.5 w-2.5 transition-transform" :class="msg.showSources ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M5 8l5 5 5-5" stroke-linecap="round" stroke-linejoin="round" />
                      </svg>
                    </button>
                    <div v-if="msg.showSources" class="mt-1.5 space-y-1 rounded-xl border border-ink-200 bg-white p-2">
                      <a
                        v-for="source in msg.sources"
                        :key="source.ref"
                        :href="source.url || '#'"
                        target="_blank"
                        rel="noopener"
                        class="block truncate rounded-lg px-2 py-1 text-[11px] text-ink-600 hover:bg-brand-50 hover:text-brand-700"
                      >
                        <span class="font-semibold text-brand-700">[{{ source.ref }}]</span>
                        {{ source.title || source.sourceTitle }}
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- Thinking indicator -->
            <div v-if="sending && (messages.length === 0 || messages[messages.length - 1].role === 'user')" class="flex gap-2.5">
              <div class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-700 to-lavender text-white">
                <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 3l1.9 4.6L18.5 9l-4.6 1.9L12 15.5l-1.9-4.6L5.5 9l4.6-1.4L12 3z" stroke-linejoin="round" />
                </svg>
              </div>
              <div class="flex items-center gap-1 rounded-2xl rounded-bl-md border border-ink-200 bg-white px-4 py-3">
                <span class="typing-dot" />
                <span class="typing-dot" style="animation-delay: 0.15s" />
                <span class="typing-dot" style="animation-delay: 0.3s" />
              </div>
            </div>
          </div>

          <!-- Disclaimer + composer -->
          <div class="border-t border-ink-200 bg-white">
            <p class="px-4 pt-2 text-[10px] leading-snug text-ink-400">
              {{ t('chatbot.disclaimer') }}
            </p>
            <div class="flex items-end gap-2 px-3 pb-3 pt-2">
              <textarea
                ref="textareaEl"
                v-model="draft"
                rows="1"
                class="input max-h-[110px] min-h-[38px] flex-1 resize-none py-2 text-sm"
                :placeholder="t('chatbot.placeholder')"
                maxlength="1000"
                @input="autoGrow"
                @keydown="onKeydown"
              />
              <button
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white transition-all hover:bg-brand-700 active:scale-95 disabled:opacity-40"
                :disabled="sending || !draft.trim()"
                @click="ask(draft)"
              >
                <svg viewBox="0 0 20 20" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 10l14-7-5.5 7L17 17 3 10zm0 0h7" stroke-linejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </section>
      </Transition>

      <button
        class="relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-brand-700 to-lavender text-white shadow-lift transition-transform hover:scale-105 active:scale-95"
        aria-label="Open chat"
        @click="toggle"
      >
        <span v-if="!open" class="absolute -right-0.5 -top-0.5 flex h-4 w-4">
          <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-60" />
          <span class="relative inline-flex h-4 w-4 rounded-full border-2 border-white bg-brand-500" />
        </span>
        <svg v-if="!open" viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8z" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <svg v-else viewBox="0 0 20 20" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 5l10 10M15 5L5 15" stroke-linecap="round" />
        </svg>
      </button>
    </div>
  </Teleport>
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
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.pop-enter-active,
.pop-leave-active {
  transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}
.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.97);
}
</style>
