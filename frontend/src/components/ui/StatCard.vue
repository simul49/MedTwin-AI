<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  hint?: string;
  tone?: 'brand' | 'amber' | 'rose' | 'emerald';
}>();
</script>

<template>
  <div class="card card-pad">
    <p class="muted">{{ label }}</p>
    <p
      class="mt-2 text-3xl font-bold"
      :class="{
        'text-brand-700': tone === 'brand',
        'text-amber-600': tone === 'amber',
        'text-rose-600': tone === 'rose',
        'text-emerald-600': tone === 'emerald',
        'text-ink-900': !tone,
      }"
    >
      {{ value }}
    </p>
    <p v-if="hint" class="mt-1 text-xs text-ink-400">{{ hint }}</p>
  </div>
</template>
