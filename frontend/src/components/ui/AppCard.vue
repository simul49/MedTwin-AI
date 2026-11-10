<script setup lang="ts">
defineProps<{
  title?: string;
  subtitle?: string;
  padded?: boolean;
}>();
</script>

<template>
  <section class="dash-card">
    <header v-if="title || $slots.actions" class="flex items-start justify-between gap-4 border-b border-ink-100 px-5 py-4 sm:px-6">
      <div>
        <h2 v-if="title" class="dash-section-title">{{ title }}</h2>
        <p v-if="subtitle" class="dash-section-sub mt-0.5">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="flex shrink-0 items-center gap-2">
        <slot name="actions" />
      </div>
    </header>
    <div :class="padded === false ? '' : 'p-5 sm:p-6'">
      <slot />
    </div>
  </section>
</template>
