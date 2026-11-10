<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{ value: number; size?: number; label?: string; caption?: string }>(),
  { size: 168, caption: 'Data completeness only — not a health assessment' },
);

const clamped = computed(() => Math.max(0, Math.min(100, Math.round(props.value))));
const radius = computed(() => props.size / 2 - 13);
const circumference = computed(() => 2 * Math.PI * radius.value);
const dash = computed(() => (clamped.value / 100) * circumference.value);
const center = computed(() => props.size / 2);
</script>

<template>
  <div class="flex flex-col items-center">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`" role="img" :aria-label="`${clamped}% complete`">
      <defs>
        <linearGradient id="gaugeGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#35bda7" />
          <stop offset="100%" stop-color="#0d7469" />
        </linearGradient>
      </defs>
      <circle
        :cx="center" :cy="center" :r="radius"
        fill="none" stroke="#d9eef0" stroke-width="13" stroke-linecap="round"
        :stroke-dasharray="`${circumference * 0.78} ${circumference}`"
        :transform="`rotate(128 ${center} ${center})`"
      />
      <circle
        :cx="center" :cy="center" :r="radius"
        fill="none" stroke="url(#gaugeGradient)" stroke-width="13" stroke-linecap="round"
        :stroke-dasharray="`${dash * 0.78} ${circumference}`"
        :transform="`rotate(128 ${center} ${center})`"
        class="transition-all duration-1000 ease-out"
      />
      <text :x="center" :y="center + 7" text-anchor="middle" font-size="30" font-weight="700" fill="#0f172a">
        {{ clamped }}%
      </text>
    </svg>
    <p v-if="label" class="mt-1 text-sm font-semibold text-ink-800">{{ label }}</p>
    <p v-if="caption" class="mt-1 max-w-[210px] text-center text-[11px] leading-snug text-ink-400">{{ caption }}</p>
  </div>
</template>
