<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { connect, consultations } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import { useRealtime } from '@/composables/useRealtime';
import type { ChatMessage, Conversation, MessageAttachment } from '@/api/types';

const { t } = useI18n();
const auth = useAuthStore();
const router = useRouter();

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

function pickFile(accept: string) {
  fileAccept.value = accept;
  fileInput.value?.click();
}

const fileAccept = ref('');
const showMore = ref(false);

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

// --- WeChat-style toolbar: emoji, voice recording, video call ----------------

const showEmoji = ref(false);
const EMOJIS = ['😀','😄','😊','🙂','😉','😍','🤗','😎','🤔','😴','😷','🤒','🤕','🥲','🙏','👍','👎','👋','💪','❤️','💔','🎉','⭐','✅','❌','💊','💉','🩺','🚑','🏥','🥗','🏃','🧘','🌙','☀️','🔥','📞','📅','⏰','📷'];

function insertEmoji(emoji: string) {
  draft.value += emoji;
  showEmoji.value = false;
}

// Voice recording via MediaRecorder; the clip auto-sends when stopped.
const recording = ref(false);
const recordSeconds = ref(0);
let mediaRecorder: MediaRecorder | null = null;
let mediaStream: MediaStream | null = null;
let recordChunks: Blob[] = [];
let recordTimer: number | undefined;

async function toggleRecording() {
  if (recording.value) {
    mediaRecorder?.stop();
    return;
  }
  if (!active.value) return;
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    sendError.value = 'Microphone access was denied — allow it in your browser settings to record voice messages.';
    return;
  }
  sendError.value = null;
  recordChunks = [];
  mediaRecorder = new MediaRecorder(mediaStream);
  mediaRecorder.ondataavailable = (e) => { if (e.data.size) recordChunks.push(e.data); };
  mediaRecorder.onstop = () => {
    recording.value = false;
    window.clearInterval(recordTimer);
    mediaStream?.getTracks().forEach((t) => t.stop());
    mediaStream = null;
    const blob = new Blob(recordChunks, { type: 'audio/webm' });
    if (blob.size < 1200 || !active.value) return; // ignore accidental taps
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const message = await connect.sendMessage(active.value!.id, '', {
          name: `voice-message-${recordSeconds.value}s.webm`,
          type: 'audio/webm',
          size: blob.size,
          data: String(reader.result ?? ''),
        });
        messages.value.push(message);
        await scroll();
      } catch (err) {
        sendError.value = err instanceof Error ? err.message : 'The voice message could not be sent.';
      }
    };
    reader.readAsDataURL(blob);
  };
  mediaRecorder.start();
  recording.value = true;
  recordSeconds.value = 0;
  recordTimer = window.setInterval(() => { recordSeconds.value += 1; }, 1000);
}

/** Join the open consultation room, or send a call request into the chat. */
async function startVideoCall() {
  if (!active.value) return;
  try {
    const items = (await consultations.list()).results;
    const counterpartId = active.value.counterpart?.id;
    const room = items.find((c) => {
      const other = c.doctor?.id === counterpartId || c.patient?.id === counterpartId;
      return other && ['PAID', 'WAITING_ROOM', 'LIVE'].includes(c.status) && (c.roomMinutesLeft ?? 0) > 0;
    });
    if (room) {
      await router.push(`/doctor/consultations/${room.id}`);
      return;
    }
    // No open room — drop a visible call request into the conversation and
    // point the patient at the video call button.
    await connect.sendMessage(active.value.id,
      `📹 ${auth.user?.name ?? 'Your clinician'} would like to start a video consultation with you. Tap the ⋯ menu → Video call to book a room and join.`);
    await scroll();
    sendError.value = null;
    callNotice.value = 'Video call request sent — the patient can now book and join the room from this chat.';
    window.setTimeout(() => { callNotice.value = null; }, 6000);
  } catch {
    await router.push('/doctor/consultations');
  }
}

const callNotice = ref<string | null>(null);
let unsubscribe: (() => void) | null = null;

onMounted(async () => {
  conversations.value = (await connect.conversations()).results;
  if (conversations.value.length) await select(conversations.value[0]);
  // Real-time messages arrive over the WebSocket; the poller stays as a fallback.
  const realtime = useRealtime();
  realtime.connect();
  unsubscribe = realtime.on('message', (payload) => {
    const conversationId = String(payload.conversationId ?? '');
    const message = payload.message as ChatMessage | undefined;
    if (!message) return;
    if (active.value && conversationId === active.value.id) {
      if (!messages.value.some((m) => m.id === message.id)) {
        messages.value.push(message);
        void scroll();
      }
    }
    void connect.conversations().then((r) => { conversations.value = r.results; });
  });
  timer = window.setInterval(async () => {
    if (active.value) messages.value = (await connect.messages(active.value.id)).messages;
  }, 30000);
});

onUnmounted(() => {
  timer && window.clearInterval(timer);
  unsubscribe?.();
  if (recording.value) mediaRecorder?.stop();
});
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
          <p v-if="callNotice" class="mb-2 rounded-xl border border-brand-200 bg-brand-50 px-2.5 py-1.5 text-[11.5px] font-medium text-brand-700">{{ callNotice }}</p>
          <p v-if="sendError" class="mb-2 text-[11.5px] font-medium text-rose-600">{{ sendError }}</p>
          <input ref="fileInput" type="file" :accept="fileAccept" class="hidden" @change="onFile" />
          <!-- Composer toolbar: media buttons left, send + more right -->
          <div class="relative flex items-center gap-1">
            <button
              type="button"
              class="btn-ghost shrink-0 rounded-full px-2 py-2"
              title="Send a photo or video (max 8 MB)"
              aria-label="Send photo or video"
              @click="pickFile('image/*,video/*')"
            >
              <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <rect x="3" y="4" width="18" height="16" rx="2.5" />
                <circle cx="9" cy="9.5" r="1.8" />
                <path d="M3.5 17l4.5-4.5 3.5 3.5 4-4 5.5 5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <button
              type="button"
              class="btn-ghost shrink-0 rounded-full px-2 py-2"
              title="Attach any file (max 8 MB)"
              aria-label="Attach file"
              @click="pickFile('audio/*,application/pdf,text/*')"
            >
              <svg class="h-[18px] w-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M21 12.5l-8.5 8.5a5 5 0 01-7-7l8.5-8.5a3.5 3.5 0 015 5L10.5 19a2 2 0 01-3-3l8-8" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <button
              type="button"
              class="btn-ghost shrink-0 rounded-full px-1.5 py-1.5"
              title="Send a GIF (max 8 MB)"
              aria-label="Send GIF"
              @click="pickFile('image/gif')"
            >
              <span class="rounded-md border-[1.5px] border-current px-1 py-0.5 text-[9px] font-extrabold tracking-tight">GIF</span>
            </button>
            <button
              type="button"
              class="btn-ghost shrink-0 rounded-full px-2 py-2 text-[17px] leading-none"
              title="Emoji"
              aria-label="Insert emoji"
              @click="showEmoji = !showEmoji; showMore = false"
            >😀</button>
            <span v-if="recording" class="ml-1 shrink-0 text-[11px] font-semibold text-rose-600">● {{ recordSeconds }}s — tap ⋯ → mic to stop</span>
            <textarea
              v-model="draft"
              rows="1"
              class="input min-h-10 min-w-0 flex-1 resize-none py-2 text-[13px]"
              placeholder="Write a message…"
              @keydown.enter.exact.prevent="send"
            />
            <button
              class="btn-primary shrink-0 rounded-full px-4 py-2 text-xs"
              type="submit"
              :disabled="!draft.trim() && !attachment && !pendingLocation"
            >{{ t('patient.assistantSend') }}</button>
            <div class="relative shrink-0">
              <button
                type="button"
                class="btn-ghost rounded-full px-2 py-2 text-[15px] font-bold leading-none"
                :class="recording ? 'text-rose-600' : ''"
                title="More: location, voice message, video call"
                aria-label="More actions"
                @click="showMore = !showMore; showEmoji = false"
              >⋯</button>
              <!-- More menu -->
              <div
                v-if="showMore"
                class="absolute bottom-11 right-0 z-10 w-56 rounded-2xl border border-ink-200 bg-white p-1.5 shadow-card"
              >
                <button
                  type="button"
                  class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-[12.5px] font-medium text-ink-700 hover:bg-ink-50"
                  @click="shareLocation(); showMore = false"
                >
                  <svg class="h-4 w-4 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path d="M12 21s-7-5.6-7-11a7 7 0 1114 0c0 5.4-7 11-7 11z" stroke-linecap="round" stroke-linejoin="round" />
                    <circle cx="12" cy="10" r="2.5" />
                  </svg>
                  Share location
                </button>
                <button
                  type="button"
                  class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-[12.5px] font-medium"
                  :class="recording ? 'text-rose-600' : 'text-ink-700 hover:bg-ink-50'"
                  @click="toggleRecording(); showMore = false"
                >
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <rect x="9" y="3" width="6" height="11" rx="3" stroke-linecap="round" />
                    <path d="M5 11a7 7 0 0014 0M12 18v3" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                  {{ recording ? `Stop & send (${recordSeconds}s)` : 'Voice message' }}
                </button>
                <button
                  type="button"
                  class="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-[12.5px] font-medium text-ink-700 hover:bg-ink-50"
                  @click="startVideoCall(); showMore = false"
                >
                  <svg class="h-4 w-4 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <rect x="3" y="6" width="12" height="12" rx="2.5" />
                    <path d="M15 10.5l5.5-3v9l-5.5-3" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                  Video call
                </button>
              </div>
            </div>
            <!-- Emoji popover -->
            <div
              v-if="showEmoji"
              class="absolute bottom-11 left-0 z-10 w-72 rounded-2xl border border-ink-200 bg-white p-2.5 shadow-card"
            >
              <div class="grid grid-cols-8 gap-1">
                <button
                  v-for="emoji in EMOJIS"
                  :key="emoji"
                  type="button"
                  class="rounded-lg px-1 py-1 text-[17px] hover:bg-ink-50"
                  @click="insertEmoji(emoji)"
                >{{ emoji }}</button>
              </div>
              <button
                type="button"
                class="mt-1.5 w-full rounded-lg py-1 text-[11px] font-semibold text-ink-400 hover:bg-ink-50"
                @click="showEmoji = false"
              >Close</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
