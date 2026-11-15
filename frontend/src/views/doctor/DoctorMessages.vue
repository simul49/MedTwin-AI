<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { connect } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import type { ChatMessage, Conversation, MessageAttachment } from '@/api/types';

const { t } = useI18n();
const auth = useAuthStore();

const conversations = ref<Conversation[]>([]);
const active = ref<Conversation | null>(null);
const messages = ref<ChatMessage[]>([]);
const draft = ref('');
const scroller = ref<HTMLElement | null>(null);
const attachment = ref<MessageAttachment | null>(null);
const pendingLocation = ref<{ lat: number; lng: number; label: string } | null>(null);
const sendError = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const MAX_ATTACHMENT = 8 * 1024 * 1024;
let timer: number | undefined;

async function select(conversation: Conversation) {
  active.value = conversation;
  messages.value = (await connect.messages(conversation.id)).messages;
  await scroll();
}

async function scroll() {
  await nextTick();
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight });
}

async function send() {
  const body = draft.value.trim();
  if ((!body && !attachment.value && !pendingLocation.value) || !active.value) return;
  const att = attachment.value;
  const loc = pendingLocation.value;
  draft.value = '';
  attachment.value = null;
  pendingLocation.value = null;
  try {
    messages.value.push(await connect.sendMessage(active.value.id, body, att ?? undefined, loc ?? undefined));
    await scroll();
  } catch (err) {
    sendError.value = err instanceof Error ? err.message : 'The message could not be sent.';
  }
}

function pickFile() {
  fileInput.value?.click();
}

function onFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (!file) return;
  if (file.size > MAX_ATTACHMENT) {
    sendError.value = 'Attachment is too large — the maximum is 8 MB.';
    return;
  }
  sendError.value = null;
  const reader = new FileReader();
  reader.onload = () => {
    attachment.value = {
      name: file.name,
      type: file.type || 'application/octet-stream',
      size: file.size,
      data: String(reader.result ?? ''),
    };
  };
  reader.readAsDataURL(file);
}

function shareLocation() {
  if (!navigator.geolocation) {
    sendError.value = 'Your browser does not support location sharing.';
    return;
  }
  sendError.value = null;
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      pendingLocation.value = {
        lat: Number(pos.coords.latitude.toFixed(6)),
        lng: Number(pos.coords.longitude.toFixed(6)),
        label: 'Shared location',
      };
    },
    () => { sendError.value = 'Location access was denied — allow it in your browser settings to share your position.'; },
    { enableHighAccuracy: false, timeout: 10000 },
  );
}

function attachmentSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}

/** Split text into plain / link segments so URLs become clickable. */
function linkSegments(text: string): Array<{ kind: 'text' | 'link'; value: string }> {
  const out: Array<{ kind: 'text' | 'link'; value: string }> = [];
  const re = /https?:\/\/[^\s<>"')\]]+/g;
  let last = 0;
  for (const m of text.matchAll(re)) {
    if (m.index! > last) out.push({ kind: 'text', value: text.slice(last, m.index) });
    out.push({ kind: 'link', value: m[0] });
    last = m.index! + m[0].length;
  }
  if (last < text.length) out.push({ kind: 'text', value: text.slice(last) });
  return out.length ? out : [{ kind: 'text', value: text }];
}

function mapsEmbed(lat: number, lng: number): string {
  return `https://maps.google.com/maps?q=${lat},${lng}&z=15&output=embed`;
}

onMounted(async () => {
  conversations.value = (await connect.conversations()).results;
  if (conversations.value.length) await select(conversations.value[0]);
  timer = window.setInterval(async () => {
    if (active.value) messages.value = (await connect.messages(active.value.id)).messages;
  }, 10000);
});

onUnmounted(() => timer && window.clearInterval(timer));
</script>

<template>
  <div>
    <header class="mb-6">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('doctor.navMessages') }}</h1>
    </header>

    <div class="grid gap-6 lg:grid-cols-3">
      <div class="card overflow-hidden">
        <p class="border-b border-ink-200 px-4 py-3 text-sm font-semibold">{{ t('doctor.authorizedPatients') }}</p>
        <ul v-if="conversations.length" class="divide-y divide-ink-100">
          <li v-for="conversation in conversations" :key="conversation.id">
            <button
              class="flex w-full items-center gap-3 px-4 py-3 text-left"
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
          <p class="text-sm font-semibold">{{ active?.counterpart?.name ?? t('doctor.navMessages') }}</p>
        </div>

        <div ref="scroller" class="flex-1 space-y-3 overflow-y-auto p-4">
          <p v-if="!active" class="muted">{{ t('common.empty') }}</p>
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
              <div v-if="message.attachments?.length" class="space-y-1.5">
                <template v-for="file in message.attachments" :key="file.name">
                  <template v-if="file.type === 'application/geo'">
                    <iframe
                      :src="mapsEmbed(file.lat ?? 0, file.lng ?? 0)"
                      class="h-40 w-72 max-w-full rounded-xl border border-white/20"
                      loading="lazy"
                      :title="file.name"
                    />
                    <a :href="file.data" target="_blank" rel="noopener" class="flex items-center gap-1.5 text-[11px] font-semibold underline">
                      <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path d="M12 21s-7-5.6-7-11a7 7 0 1114 0c0 5.4-7 11-7 11z" stroke-linecap="round" stroke-linejoin="round" />
                        <circle cx="12" cy="10" r="2.5" />
                      </svg>
                      {{ file.name }} — open in Maps
                    </a>
                  </template>
                  <img
                    v-else-if="file.type.startsWith('image/')"
                    :src="file.data"
                    :alt="file.name"
                    class="max-h-56 w-auto max-w-full rounded-xl border border-white/20"
                  />
                  <video
                    v-else-if="file.type.startsWith('video/')"
                    :src="file.data"
                    controls
                    class="max-h-56 w-auto max-w-full rounded-xl"
                  />
                  <audio v-else-if="file.type.startsWith('audio/')" :src="file.data" controls class="w-60" />
                  <a
                    v-else
                    :href="file.data"
                    :download="file.name"
                    class="flex items-center gap-2 rounded-xl bg-white/15 px-2.5 py-2 text-xs font-medium hover:bg-white/25"
                  >
                    <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                      <path d="M14 3v5h5M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                    <span class="min-w-0">
                      <span class="block max-w-44 truncate">{{ file.name }}</span>
                      <span class="block text-[10px] opacity-70">{{ attachmentSize(file.size) }} · download</span>
                    </span>
                  </a>
                </template>
              </div>
              <p v-if="message.body" class="mt-1 text-sm first:mt-0">
                <template v-for="(seg, i) in linkSegments(message.body)" :key="i">
                  <a
                    v-if="seg.kind === 'link'"
                    :href="seg.value"
                    target="_blank"
                    rel="noopener"
                    class="underline"
                    :class="message.senderId === auth.user?.id ? 'text-white' : 'text-brand-600'"
                  >{{ seg.value }}</a>
                  <template v-else>{{ seg.value }}</template>
                </template>
              </p>
              <p class="mt-1 text-[11px] opacity-70">{{ formatDateTime(message.createdAt, 'en') }}</p>
            </div>
          </div>
        </div>

        <form v-if="active" class="border-t border-ink-200 p-3" @submit.prevent="send">
          <div
            v-if="attachment || pendingLocation"
            class="mb-2 flex items-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-2.5 py-1.5"
          >
            <template v-if="attachment">
              <span class="text-[11px] font-semibold text-brand-700">{{ attachment.name }}</span>
              <span class="text-[10px] text-ink-400">{{ attachmentSize(attachment.size) }}</span>
            </template>
            <template v-else>
              <svg class="h-3.5 w-3.5 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M12 21s-7-5.6-7-11a7 7 0 1114 0c0 5.4-7 11-7 11z" stroke-linecap="round" stroke-linejoin="round" />
                <circle cx="12" cy="10" r="2.5" />
              </svg>
              <span class="text-[11px] font-semibold text-brand-700">{{ pendingLocation!.lat }}, {{ pendingLocation!.lng }}</span>
            </template>
            <button
              type="button"
              class="ml-auto text-[11px] font-semibold text-ink-500 hover:text-rose-600"
              @click="attachment = null; pendingLocation = null"
            >Remove</button>
          </div>
          <p v-if="sendError" class="mb-2 text-[11.5px] font-medium text-rose-600">{{ sendError }}</p>
          <input ref="fileInput" type="file" class="hidden" @change="onFile" />
          <div class="flex items-end gap-2">
            <button
              type="button"
              class="btn-ghost shrink-0 px-2.5 py-2.5"
              title="Attach a photo, video, audio or PDF (max 8 MB)"
              aria-label="Attach file"
              @click="pickFile"
            >
              <svg class="h-4.5 w-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M21 12.5l-8.5 8.5a5 5 0 01-7-7l8.5-8.5a3.5 3.5 0 015 5L10.5 19a2 2 0 01-3-3l8-8" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <button
              type="button"
              class="btn-ghost shrink-0 px-2.5 py-2.5"
              title="Share your current location"
              aria-label="Share location"
              @click="shareLocation"
            >
              <svg class="h-4.5 w-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M12 21s-7-5.6-7-11a7 7 0 1114 0c0 5.4-7 11-7 11z" stroke-linecap="round" stroke-linejoin="round" />
                <circle cx="12" cy="10" r="2.5" />
              </svg>
            </button>
            <textarea
              v-model="draft"
              rows="1"
              class="input min-h-10 flex-1 resize-none py-2 text-[13px]"
              placeholder="Write a message…"
              @keydown.enter.exact.prevent="send"
            />
            <button
              class="btn-primary shrink-0 px-4 py-2 text-xs"
              type="submit"
              :disabled="!draft.trim() && !attachment && !pendingLocation"
            >{{ t('patient.assistantSend') }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
