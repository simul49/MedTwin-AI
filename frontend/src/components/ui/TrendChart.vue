<script setup lang="ts">
import { computed } from 'vue';

type Kind = 'bars' | 'line' | 'wave';

const props = withDefaults(
  defineProps<{ values: number[]; kind?: Kind; height?: number; color?: string; labels?: string[] }>(),
  { kind: 'line', height: 130, color: '#101585' },
);

const W = 400;
const H = computed(() => props.height);
const data = computed(() => (props.values.length ? props.values : [12, 24, 18, 32, 28, 44, 38, 52, 46, 60, 55, 68]));
const max = computed(() => Math.max(...data.value, 1) * 1.15);

const points = computed(() =>
  data.value.map((v, i) => ({
    x: 12 + (i * (W - 24)) / Math.max(1, data.value.length - 1),
    y: H.value - 14 - (v / max.value) * (H.value - 30),
    v,
  })),
);

const polyline = computed(() => points.value.map((p) => `${p.x},${p.y}`).join(' '));
const area = computed(() => {
  const last = points.value[points.value.length - 1];
  return `M ${points.value[0]?.x ?? 0},${H.value - 10} L ${polyline.value.replaceAll(' ', ' L ')} L ${last?.x ?? W},${H.value - 10} Z`;
});
const barWidth = computed(() => Math.max(6, (W - 24) / Math.max(1, data.value.length) - 9));
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="h-full w-full" preserveAspectRatio="none" role="img" aria-label="Trend chart">
    <defs>
      <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" :stop-color="color" stop-opacity="0.28" />
        <stop offset="100%" :stop-color="color" stop-opacity="0.01" />
      </linearGradient>
    </defs>

    <g v-for="n in 4" :key="`grid-${n}`">
      <line x1="0" :x2="W" :y1="(H / 4) * n" :y2="(H / 4) * n" stroke="#eef2f6" stroke-width="1" />
    </g>

    <template v-if="kind === 'bars'">
      <rect
        v-for="(p, i) in points"
        :key="`bar-${i}`"
        :x="p.x - barWidth / 2"
        :y="p.y"
        :width="barWidth"
        :height="H - 12 - p.y"
        rx="4"
        :fill="i % 3 === 0 ? '#A78BFA' : color"
        opacity="0.9"
      />
    </template>

    <template v-else-if="kind === 'wave'">
      <line x1="0" :x2="W" :y1="H / 2" :y2="H / 2" stroke="#dce9ed" stroke-width="1" />
      <g v-for="(p, i) in data.flatMap((v, idx) => [v * 0.55, v, v * 0.4])" :key="`wave-${i}`">
        <line
          :x1="12 + (i * (W - 24)) / Math.max(1, data.length * 3 - 1)"
          :x2="12 + (i * (W - 24)) / Math.max(1, data.length * 3 - 1)"
          :y1="H / 2 - (p / max) * (H / 2 - 8)"
          :y2="H / 2 + (p / max) * (H / 2 - 8)"
          :stroke="p > max * 0.6 ? color : '#9ee8da'"
          stroke-width="2"
          stroke-linecap="round"
        />
      </g>
    </template>

    <template v-else>
      <path :d="area" fill="url(#chartFill)" />
      <polyline :points="polyline" fill="none" :stroke="color" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      <circle
        v-for="(p, i) in points"
        :key="`dot-${i}`"
        :cx="p.x" :cy="p.y" r="3.5"
        fill="#fff" :stroke="color" stroke-width="2"
      />
    </template>
  </svg>
</template>
