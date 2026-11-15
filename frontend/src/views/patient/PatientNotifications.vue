<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';
import { connect } from '@/api/endpoints';
import { useRealtime } from '@/composables/useRealtime';
import { formatDateTime } from '@/composables/useAsync';
import EmptyState from '@/components/ui/EmptyState.vue';
import type { NotificationItem } from '@/api/types';

const { t } = useI18n();
const ui = useUiStore();
const router = useRouter();

const items = ref<NotificationItem[]>([]);
const unread = ref(0);
const loading = ref(false);
const tab = ref<'all' | 'unread'>('all');

async function load() {
  loading.value = true;
  try {
    const result = await connect.notifications();
    items.value = result.results;
    unread.value = result.unread;
  } finally {
    loading.value = false;
  }
}

const visible = computed(() =>
  tab.value === 'unread' ? items.value.filter((item) => !item.isRead) : items.value,
);

interface TypeStyle {
  icon: string;
  tile: string;
  label: string;
}

const TYPE_STYLES: Record<string, TypeStyle> = {
  APPOINTMENT_REQUEST: { icon: 'M7 3h10v18H7zM7 8h10M10 12h4M10 16h4', tile: 'bg-brand-50 text-brand-700', label: 'Appointment' },
  APPOINTMENT_UPDATE: { icon: 'M7 3h10v18H7zM7 8h10M10 12h4M10 16h4', tile: 'bg-brand-50 text-brand-700', label: 'Appointment' },
  CONSULTATION_REQUEST: { icon: 'M15 10l5-3v10l-5-3M3 7h11v10H3z', tile: 'bg-violet-50 text-violet-700', label: 'Consultation' },
  CONSULTATION_UPDATE: { icon: 'M15 10l5-3v10l-5-3M3 7h11v10H3z', tile: 'bg-violet-50 text-violet-700', label: 'Consultation' },
  PAYMENT_RECEIVED: { icon: 'M3 7h18v10H3zM3 11h18M7 14h3', tile: 'bg-emerald-50 text-emerald-700', label: 'Payment' },
  CONSENT_REQUEST: { icon: 'M12 3l8 3v6c0 4.5-3.2 7.6-8 9-4.8-1.4-8-4.5-8-9V6z', tile: 'bg-amber-50 text-amber-700', label: 'Consent' },
  CONSENT_GRANTED: { icon: 'M12 3l8 3v6c0 4.5-3.2 7.6-8 9-4.8-1.4-8-4.5-8-9V6zM9 12l2 2 4-4', tile: 'bg-emerald-50 text-emerald-700', label: 'Consent' },
  PRESCRIPTION_READY: { icon: 'M6 2h8l4 4v16H6zM14 2v5h5M9 13h6M9 17h6', tile: 'bg-sky-50 text-sky-700', label: 'Prescription' },
};

function styleFor(type: string): TypeStyle {
  return TYPE_STYLES[type] ?? { icon: 'M12 3a6 6 0 016 6v4l2 3H4l2-3V9a6 6 0 016-6zM10 19a2 2 0 004 0', tile: 'bg-surface-100 text-ink-600', label: 'Update' };
}

function relativeTime(value: string | null): string {
  if (!value) return '';
  const then = new Date(value).getTime();
  const diff = Date.now() - then;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days} days ago`;
  return formatDateTime(value, ui.locale);
}

async function open(item: NotificationItem) {
  if (!item.isRead) {
    await connect.markRead(item.id);
    unread.value = Math.max(0, unread.value - 1);
    item.isRead = true;
  }
  if (item.link) router.push(item.link);
}

async function markRead(item: NotificationItem) {
  await connect.markRead(item.id);
  await load();
}

async function markAll() {
  await connect.markAllRead();
  await load();
}

// Live: new notifications arrive over WebSocket.
const realtime = useRealtime();
let unsubscribe: (() => void) | null = null;

onMounted(() => {
  void load();
  realtime.connect();
  unsubscribe = realtime.on('notification', () => void load());
});

onUnmounted(() => unsubscribe?.());
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Activity &amp; alerts</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">Notifications</h1>
        <p class="mt-2 text-[14px] text-ink-500">
          Appointment updates, payments, consent changes and results — in one place.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="unread" class="chip bg-brand-50 text-brand-700">{{ unread }} unread</span>
        <button v-if="unread" class="btn-secondary text-xs" @click="markAll">{{ t('patient.markAllRead') }}</button>
      </div>
    </div>

    <div class="mb-4 flex gap-2">
      <button
        class="rounded-full px-3.5 py-1.5 text-[12px] font-semibold transition-colors"
        :class="tab === 'all' ? 'bg-ink-900 text-white' : 'bg-surface-100 text-ink-600 hover:bg-surface-200'"
        @click="tab = 'all'"
      >
        All <span class="opacity-60">{{ items.length }}</span>
      </button>
      <button
        class="rounded-full px-3.5 py-1.5 text-[12px] font-semibold transition-colors"
        :class="tab === 'unread' ? 'bg-ink-900 text-white' : 'bg-surface-100 text-ink-600 hover:bg-surface-200'"
        @click="tab = 'unread'"
      >
        Unread <span class="opacity-60">{{ unread }}</span>
      </button>
    </div>

    <div class="dash-card overflow-hidden">
      <div v-if="loading" class="h-40 animate-pulse bg-ink-100" />
      <EmptyState
        v-else-if="!visible.length"
        :title="tab === 'unread' ? 'You are all caught up' : t('common.empty')"
        icon="◔"
      />
      <ul v-else class="divide-y divide-ink-100">
        <li v-for="item in visible" :key="item.id">
          <div
            class="flex cursor-pointer items-start gap-4 px-5 py-4 transition-colors hover:bg-surface-50"
            :class="item.isRead ? '' : 'bg-brand-50/40'"
            @click="open(item)"
          >
            <span
              class="dash-icon-tile shrink-0"
              :class="styleFor(item.type).tile"
              aria-hidden="true"
            >
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <path :d="styleFor(item.type).icon" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <p class="text-[14px]" :class="item.isRead ? 'font-medium text-ink-800' : 'font-bold text-ink-900'">
                  {{ item.title }}
                </p>
                <span class="chip bg-surface-100 text-[10px] text-ink-500">{{ styleFor(item.type).label }}</span>
                <span v-if="!item.isRead" class="h-2 w-2 rounded-full bg-brand-600" aria-label="unread" />
              </div>
              <p class="muted mt-0.5 text-[13px]">{{ item.body }}</p>
              <p class="mt-1.5 text-[11px] text-ink-400">
                {{ relativeTime(item.createdAt) }} · {{ formatDateTime(item.createdAt, ui.locale) }}
              </p>
            </div>
            <div class="flex shrink-0 items-center gap-2 self-center">
              <button
                v-if="!item.isRead"
                class="btn-ghost text-xs"
                @click.stop="markRead(item)"
              >
                Mark read
              </button>
              <svg v-if="item.link" class="h-4 w-4 text-ink-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <path d="M9 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
