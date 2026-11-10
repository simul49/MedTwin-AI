<script setup lang="ts">
defineProps<{
  title: string;
  body?: string;
  icon?: string;
}>();
</script>

<template>
  <div class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-ink-300 bg-white/60 px-6 py-12 text-center">
    <div class="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-xl text-brand-600">
      {{ icon ?? '◍' }}
    </div>
    <p class="font-semibold text-ink-800">{{ title }}</p>
    <p v-if="body" class="muted mt-1 max-w-sm">{{ body }}</p>
    <div v-if="$slots.default" class="mt-4">
      <slot />
    </div>
  </div>
</template>
