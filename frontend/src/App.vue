<script setup lang="ts">
import { onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';

const auth = useAuthStore();
const ui = useUiStore();

const toneIcon: Record<string, string> = {
  success: 'M9.5 12.5l2 2 3.5-4',
  error: 'M12 8v4.5M12 16v.5',
  info: 'M12 8v4.5M12 16v.5',
};
const toneStyle: Record<string, string> = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  error: 'border-rose-200 bg-rose-50 text-rose-800',
  info: 'border-brand-200 bg-brand-50 text-brand-800',
};
const toneDot: Record<string, string> = {
  success: 'bg-emerald-500',
  error: 'bg-rose-500',
  info: 'bg-brand-500',
};

onMounted(() => {
  // Restore the session (if any) before the first route guard runs.
  void auth.bootstrap();
});
</script>

<template>
  <RouterView v-slot="{ Component }">
    <Suspense>
      <component :is="Component" />
    </Suspense>
  </RouterView>

  <!-- Global toast host -->
  <div class="pointer-events-none fixed right-4 top-4 z-[60] flex w-80 flex-col gap-2">
    <Transition
      v-for="toast in ui.toasts"
      :key="toast.id"
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-2 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
      appear
    >
      <div
        class="pointer-events-auto flex items-start gap-2.5 rounded-2xl border px-3.5 py-3 text-[12.5px] font-medium shadow-card"
        :class="toneStyle[toast.tone]"
      >
        <span class="mt-1.5 h-2 w-2 shrink-0 rounded-full" :class="toneDot[toast.tone]" />
        <span class="leading-relaxed">{{ toast.message }}</span>
      </div>
    </Transition>
  </div>
</template>
