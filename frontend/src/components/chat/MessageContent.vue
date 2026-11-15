<script setup lang="ts">
import { computed } from 'vue';
import type { ChatMessage, MessageAttachment } from '@/api/types';

const props = defineProps<{ message: ChatMessage; own: boolean }>();

const URL_RE = /(https?:\/\/[^\s<>")\]]+)/g;
interface Part { text: string; url: string | null }

/** Split the body into plain-text and URL segments for safe clickable links. */
const parts = computed<Part[]>(() => {
  const body = props.message.body;
  if (!body) return [];
  const out: Part[] = [];
  let last = 0;
  for (const match of body.matchAll(URL_RE)) {
    const index = match.index ?? 0;
    if (index > last) out.push({ text: body.slice(last, index), url: null });
    out.push({ text: match[0], url: match[0] });
    last = index + match[0].length;
  }
  if (last < body.length) out.push({ text: body.slice(last), url: null });
  return out;
});

const location = computed(() => {
  const m = props.message.metadata as { type?: string; lat?: number; lng?: number; label?: string } | undefined;
  return m && m.type === 'location' && typeof m.lat === 'number' && typeof m.lng === 'number' ? m : null;
});

const attachments = computed<MessageAttachment[]>(() => props.message.attachments ?? []);

function attachmentSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}
</script>

<template>
  <!-- Shared location: embedded map card -->
  <div v-if="location" class="mb-1.5 w-72 max-w-full">
    <iframe
      :src="`https://maps.google.com/maps?q=${location.lat},${location.lng}&z=15&output=embed`"
      class="h-40 w-full rounded-xl border"
      :class="own ? 'border-white/25' : 'border-ink-200'"
      loading="lazy"
      :title="`Map of ${location.label}`"
    />
    <a
      :href="`https://www.google.com/maps?q=${location.lat},${location.lng}`"
      target="_blank"
      rel="noopener noreferrer"
      class="mt-1.5 flex items-center gap-1.5 rounded-xl px-2.5 py-2 text-[12px] font-semibold"
      :class="own ? 'bg-white/15 hover:bg-white/25' : 'bg-surface-100 hover:bg-ink-100'"
    >
      <svg class="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
        <path d="M12 21s-7-6.1-7-11a7 7 0 0114 0c0 4.9-7 11-7 11z" stroke-linecap="round" stroke-linejoin="round" />
        <circle cx="12" cy="10" r="2.5" />
      </svg>
      <span class="min-w-0 truncate">{{ location.label || 'Shared location' }} · open in Google Maps</span>
    </a>
  </div>

  <!-- File attachments: image / video / audio / download card -->
  <div v-if="attachments.length" class="space-y-1.5">
    <template v-for="file in attachments" :key="file.name">
      <img
        v-if="file.type.startsWith('image/')"
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
        class="flex items-center gap-2 rounded-xl px-2.5 py-2 text-[12px] font-medium"
        :class="own ? 'bg-white/15 hover:bg-white/25' : 'bg-surface-100 hover:bg-ink-100'"
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

  <!-- Body with clickable links -->
  <p v-if="message.body" class="mt-1 whitespace-pre-wrap text-[13px] leading-relaxed first:mt-0">
    <template v-for="(part, i) in parts" :key="i">
      <a
        v-if="part.url"
        :href="part.url"
        target="_blank"
        rel="noopener noreferrer"
        class="underline decoration-dotted underline-offset-2"
        :class="own ? 'text-white hover:text-white/85' : 'text-brand-600 hover:text-brand-700'"
      >{{ part.text }}</a>
      <template v-else>{{ part.text }}</template>
    </template>
  </p>
</template>
