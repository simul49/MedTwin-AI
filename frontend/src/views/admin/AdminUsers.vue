<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { admin } from '@/api/endpoints';
import type { User } from '@/api/types';
import StatusBadge from '@/components/ui/StatusBadge.vue';

const { t } = useI18n();

const users = ref<User[]>([]);
const role = ref('');
const query = ref('');
const loading = ref(true);

const roleCounts = computed(() => ({
  patients: users.value.filter((u) => u.role === 'PATIENT').length,
  doctors: users.value.filter((u) => u.role === 'DOCTOR').length,
  admins: users.value.filter((u) => u.role === 'ADMIN').length,
}));

async function load() {
  loading.value = true;
  try {
    users.value = (await admin.users({ role: role.value || undefined, q: query.value || undefined })).results;
  } finally {
    loading.value = false;
  }
}

async function toggleActive(user: User) {
  await admin.updateUser(user.id, { isActive: !user.isActive });
  await load();
}

async function changeRole(user: User, nextRole: string) {
  await admin.updateUser(user.id, { role: nextRole });
  await load();
}

async function setVerification(user: User, status: string) {
  await admin.updateUser(user.id, { verificationStatus: status });
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <header class="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">User management</p>
        <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">{{ t('admin.users') }}</h1>
        <p class="mt-1 text-[13px] text-ink-500">{{ t('admin.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-2 text-[11px] font-semibold">
        <span class="chip bg-brand-50 text-brand-700">{{ roleCounts.patients }} patients</span>
        <span class="chip bg-lavender-light text-lavender-dark">{{ roleCounts.doctors }} doctors</span>
        <span class="chip bg-surface-100 text-ink-600">{{ roleCounts.admins }} admins</span>
      </div>
    </header>

    <div class="dash-card overflow-hidden">
      <!-- Toolbar -->
      <div class="flex flex-wrap items-center gap-2.5 border-b border-ink-100 bg-surface-50/60 px-4 py-3">
        <div class="relative">
          <svg class="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M15.5 15.5 21 21M10 18a8 8 0 100-16 8 8 0 000 16z" stroke-linecap="round" />
          </svg>
          <input
            v-model="query"
            class="input w-56 py-1.5 text-xs pl-9"
            :placeholder="t('admin.searchUsers')"
            @keyup.enter="load"
          />
        </div>
        <select v-model="role" class="input w-36 py-1.5 text-xs" @change="load">
          <option value="">{{ t('common.all') }}</option>
          <option value="PATIENT">PATIENT</option>
          <option value="DOCTOR">DOCTOR</option>
          <option value="ADMIN">ADMIN</option>
        </select>
        <button class="btn-secondary ml-auto px-3 py-1.5 text-xs" @click="load">{{ t('common.refresh') }}</button>
      </div>

      <div v-if="loading" class="shimmer h-56 animate-pulse bg-ink-50" />

      <div v-else-if="!users.length" class="px-4 py-14 text-center">
        <p class="text-[14px] font-semibold text-ink-700">No users match this view</p>
        <p class="mt-1 text-[12px] text-ink-400">Try a different search term or role filter.</p>
      </div>

      <ul v-else class="divide-y divide-ink-100">
        <li v-for="user in users" :key="user.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-surface-50/70">
          <div class="flex min-w-0 items-center gap-3">
            <span
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white shadow-card"
              :style="{ backgroundColor: user.avatarColor }"
            >
              {{ user.initials }}
            </span>
            <div class="min-w-0">
              <p class="text-[14px] font-semibold text-ink-900">{{ user.name }}</p>
              <p class="mt-0.5 truncate text-[12px] text-ink-400">{{ user.email }}</p>
            </div>
          </div>

          <div class="flex shrink-0 flex-wrap items-center justify-end gap-2">
            <StatusBadge :status="user.role" />
            <span
              class="chip font-semibold"
              :class="user.isActive ? 'bg-brand-50 text-brand-700' : 'bg-rose-50 text-rose-600'"
            >
              <span class="h-1.5 w-1.5 rounded-full" :class="user.isActive ? 'bg-brand-500' : 'bg-rose-400'" />
              {{ user.isActive ? t('status.ACTIVE') : t('status.REVOKED') }}
            </span>

            <select
              v-if="user.role === 'DOCTOR'"
              class="input w-32 py-1.5 text-xs"
              :class="(user.doctorProfile?.verificationStatus ?? 'PENDING') === 'VERIFIED' ? 'border-brand-300' : ''"
              :value="user.doctorProfile?.verificationStatus ?? 'PENDING'"
              @change="setVerification(user, ($event.target as HTMLSelectElement).value)"
            >
              <option value="PENDING">{{ t('status.PENDING') }}</option>
              <option value="VERIFIED">{{ t('doctor.verified') }}</option>
              <option value="REJECTED">{{ t('status.REJECTED') }}</option>
            </select>

            <select
              class="input w-28 py-1.5 text-xs"
              :value="user.role"
              @change="changeRole(user, ($event.target as HTMLSelectElement).value)"
            >
              <option value="PATIENT">PATIENT</option>
              <option value="DOCTOR">DOCTOR</option>
              <option value="ADMIN">ADMIN</option>
            </select>

            <button
              class="rounded-lg border px-3 py-1.5 text-[11px] font-semibold transition-colors"
              :class="user.isActive ? 'border-rose-200 text-rose-600 hover:bg-rose-50' : 'border-brand-200 text-brand-700 hover:bg-brand-50'"
              @click="toggleActive(user)"
            >
              {{ user.isActive ? 'Disable' : 'Enable' }}
            </button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
