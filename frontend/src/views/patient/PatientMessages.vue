<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { connect } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import type { ChatMessage, Conversation } from '@/api/types';

const { t } = useI18n();
const auth = useAuthStore();

const conversations = ref<Conversation[]>([]);
const active = ref<Conversation | null>(null);
const messages = ref<ChatMessage[]>([]);
const draft = ref('');
const loading = ref(false);
const error = ref<string | null>(null);
const scroller = ref<HTMLElement | null>(null);
let timer: number | undefined;

async function loadConversations() {
  try {
    conversations.value = (await connect.conversations()).results;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
}

async function select(conversation: Conversation) {
  active.value = conversation;
  loading.value = true;
  try {
    const result = await connect.messages(conversation.id);
    messages.value = result.messages;
    await scroll();
  } finally {
    loading.value = false;
  }
}

async function scroll() {
  await nextTick();
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight });
}

async function send() {
  if (!draft.value.trim() || !active.value) return;
  const body = draft.value.trim();
  draft.value = '';
  const message = await connect.sendMessage(active.value.id, body);
  messages.value.push(message);
  await scroll();
}

onMounted(async () => {
  await loadConversations();
  if (conversations.value.length) await select(conversations.value[0]);
  timer = window.setInterval(async () => {
    if (active.value) messages.value = (await connect.messages(active.value.id)).messages;
  }, 10000);
});

onUnmounted(() => {
  if (timer) window.clearInterval(timer);
});
</script>

<template>
  <div>
    <header class="mb-6">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('patient.messagesTitle') }}</h1>
    </header>

    <p v-if="error" class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <div class="grid gap-6 lg:grid-cols-3">
      <div class="card overflow-hidden">
        <p class="border-b border-ink-200 px-4 py-3 text-sm font-semibold">{{ t('patient.messagesTitle') }}</p>
        <ul v-if="conversations.length" class="divide-y divide-ink-100">
          <li v-for="conversation in conversations" :key="conversation.id">
            <button
              class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors"
              :class="active?.id === conversation.id ? 'bg-brand-50' : 'hover:bg-ink-50'"
              @click="select(conversation)"
            >
              <span
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                :style="{ backgroundColor: conversation.counterpart?.avatarColor ?? '#2563eb' }"
              >
                {{ conversation.counterpart?.initials ?? '—' }}
              </span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium">{{ conversation.counterpart?.name ?? conversation.title }}</span>
                <span class="block truncate text-xs text-ink-400">{{ conversation.lastMessage }}</span>
              </span>
              <span v-if="conversation.unread" class="chip bg-rose-600 text-white">{{ conversation.unread }}</span>
            </button>
          </li>
        </ul>
        <p v-else class="muted p-4">{{ t('common.empty') }}</p>
      </div>

      <div class="card flex h-[30rem] flex-col lg:col-span-2">
        <div class="border-b border-ink-200 px-4 py-3">
          <p class="text-sm font-semibold">{{ active?.counterpart?.name ?? t('patient.messagesTitle') }}</p>
          <p v-if="active?.counterpart?.specialization" class="muted">{{ active.counterpart.specialization }}</p>
        </div>

        <div ref="scroller" class="flex-1 space-y-3 overflow-y-auto p-4">
          <p v-if="!active" class="muted">{{ t('common.empty') }}</p>
          <div v-else-if="loading" class="h-20 animate-pulse rounded-xl bg-ink-100" />
          <template v-else>
            <div
              v-for="message in messages"
              :key="message.id"
              class="flex"
              :class="message.senderId === auth.user?.id ? 'justify-end' : 'justify-start'"
            >
              <div
                class="max-w-[80%] rounded-2xl px-4 py-2.5"
                :class="message.senderId === auth.user?.id ? 'bg-brand-600 text-white' : 'bg-ink-100 text-ink-900'"
              >
                <p class="text-sm">{{ message.body }}</p>
                <p class="mt-1 text-[11px] opacity-70">{{ formatDateTime(message.createdAt, 'en') }}</p>
              </div>
            </div>
          </template>
        </div>

        <form v-if="active" class="flex gap-2 border-t border-ink-200 p-3" @submit.prevent="send">
          <input v-model="draft" class="input" :placeholder="t('patient.messagesTitle')" />
          <button class="btn-primary" type="submit">{{ t('patient.assistantSend') }}</button>
        </form>
      </div>
    </div>
  </div>
</template>
