<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { admin } from '@/api/endpoints';
import type { User } from '@/api/types';
import AppCard from '@/components/ui/AppCard.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';

const { t } = useI18n();

const users = ref<User[]>([]);
const role = ref('');
const query = ref('');
const loading = ref(true);

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
    <header class="mb-6">
      <h1 class="text-2xl font-bold sm:text-3xl">{{ t('admin.users') }}</h1>
      <p class="muted mt-1">{{ t('admin.subtitle') }}</p>
    </header>

    <AppCard>
      <template #actions>
        <select v-model="role" class="input max-w-40" @change="load">
          <option value="">{{ t('common.all') }}</option>
          <option value="PATIENT">PATIENT</option>
          <option value="DOCTOR">DOCTOR</option>
          <option value="ADMIN">ADMIN</option>
        </select>
        <input v-model="query" class="input max-w-56" :placeholder="t('admin.searchUsers')" @keyup.enter="load" />
      </template>

      <div v-if="loading" class="h-40 animate-pulse rounded-xl bg-ink-100" />

      <ul v-else class="divide-y divide-ink-100">
        <li v-for="user in users" :key="user.id" class="flex flex-wrap items-center justify-between gap-3 py-3">
          <div class="flex min-w-0 items-center gap-3">
            <span
              class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
              :style="{ backgroundColor: user.avatarColor }"
            >
              {{ user.initials }}
            </span>
            <div class="min-w-0">
              <p class="text-sm font-medium">{{ user.name }}</p>
              <p class="muted mt-0.5 truncate">{{ user.email }}</p>
            </div>
          </div>

          <div class="flex shrink-0 flex-wrap items-center gap-2">
            <StatusBadge :status="user.role" />
            <span class="chip" :class="user.isActive ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'">
              {{ user.isActive ? t('status.ACTIVE') : t('status.REVOKED') }}
            </span>

            <select
              v-if="user.role === 'DOCTOR'"
              class="input max-w-36 py-1.5 text-xs"
              :value="user.doctorProfile?.verificationStatus ?? 'PENDING'"
              @change="setVerification(user, ($event.target as HTMLSelectElement).value)"
            >
              <option value="PENDING">{{ t('status.PENDING') }}</option>
              <option value="VERIFIED">{{ t('doctor.verified') }}</option>
              <option value="REJECTED">{{ t('status.REJECTED') }}</option>
            </select>

            <select
              class="input max-w-32 py-1.5 text-xs"
              :value="user.role"
              @change="changeRole(user, ($event.target as HTMLSelectElement).value)"
            >
              <option value="PATIENT">PATIENT</option>
              <option value="DOCTOR">DOCTOR</option>
              <option value="ADMIN">ADMIN</option>
            </select>

            <button class="btn-secondary px-3 py-1.5 text-xs" @click="toggleActive(user)">
              {{ t('admin.toggleActive') }}
            </button>
          </div>
        </li>
      </ul>
    </AppCard>
  </div>
</template>
