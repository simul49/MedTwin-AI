<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useRealtime } from '@/composables/useRealtime';
import type { Consultation } from '@/api/types';

const router = useRouter();
const auth = useAuthStore();
const realtime = useRealtime();

/** Doctor side: a paid patient is waiting in the room — ring. */
const call = ref<Consultation | null>(null);
const callerName = ref('');
/** Both sides: non-blocking toast for payment / join events. */
const toast = ref<string | null>(null);

let offUpdate: (() => void) | null = null;
let audioCtx: AudioContext | null = null;
let ringTimer: number | undefined;
let toastTimer: number | undefined;

function showRing(consultation: Consultation) {
  if (call.value) return; // already ringing
  call.value = consultation;
  callerName.value = consultation.patient?.name ?? 'A patient';
  try {
    audioCtx = audioCtx ?? new AudioContext();
    ringTimer = window.setInterval(() => {
      if (!audioCtx) return;
      const t0 = audioCtx.currentTime;
      [880, 1108.7].forEach((freq, i) => {
        const osc = audioCtx!.createOscillator();
        const gain = audioCtx!.createGain();
        osc.type = 'sine';
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.001, t0 + i * 0.35);
        gain.gain.exponentialRampToValueAtTime(0.16, t0 + i * 0.35 + 0.04);
        gain.gain.exponentialRampToValueAtTime(0.001, t0 + i * 0.35 + 0.3);
        osc.connect(gain);
        gain.connect(audioCtx!.destination);
        osc.start(t0 + i * 0.35);
        osc.stop(t0 + i * 0.35 + 0.32);
      });
    }, 2200);
  } catch {
    // audio blocked until first user interaction — visual ring still shows
  }
}

function stopRing() {
  if (ringTimer) window.clearInterval(ringTimer);
  ringTimer = undefined;
}

function accept() {
  const id = call.value?.id;
  stopRing();
  call.value = null;
  if (id) router.push(`/doctor/consultations/${id}`);
}

function decline() {
  stopRing();
  call.value = null;
}

function showToast(message: string) {
  toast.value = message;
  if (toastTimer) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => (toast.value = null), 8000);
}

onMounted(() => {
  offUpdate = realtime.on('consultation-update', (payload) => {
    const c = payload.consultation as Consultation | undefined;
    if (!c) return;
    if (auth.isDoctor && c.status === 'WAITING_ROOM') {
      showRing(c);
    } else if (auth.isPatient && c.status === 'LIVE') {
      showToast('Your clinician has joined the room — open Consultations to enter the call.');
    }
  });
  // Generic notification toasts render globally in App.vue; this component
  // only handles call-specific UX (ringing overlay, joined-room hint).
  realtime.connect();
});

onUnmounted(() => {
  offUpdate?.();
  stopRing();
  if (toastTimer) window.clearTimeout(toastTimer);
});
</script>

<template>
  <!-- Incoming call (doctor) -->
  <Teleport to="body">
    <div
      v-if="call"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-ink-900/70 backdrop-blur-sm"
    >
      <div class="w-[22rem] rounded-3xl border border-white/10 bg-ink-900 px-6 py-8 text-center shadow-2xl">
        <span class="relative mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-brand-600">
          <span class="absolute inset-0 animate-ping rounded-full bg-brand-600/50" />
          <svg class="h-7 w-7 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM4 21a8 8 0 0116 0" stroke-linecap="round" />
          </svg>
        </span>
        <p class="mt-4 text-[11px] font-bold uppercase tracking-widest text-white/50">Incoming consultation</p>
        <p class="mt-1 text-[18px] font-bold text-white">{{ callerName }} is waiting</p>
        <p class="mt-1 text-[12px] text-white/60">
          Paid {{ call.feeCurrency }} {{ call.feeAmount }} · room ready
        </p>
        <div class="mt-6 flex items-center justify-center gap-3">
          <button
            class="flex h-11 flex-1 items-center justify-center gap-2 rounded-full bg-brand-600 px-4 text-[13px] font-bold text-white transition-colors hover:bg-brand-500"
            @click="accept"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M3 10c5-4 13-4 18 0l-2.5 3-3.5-1v-3.5M3 10l2.5 3 3.5-1V8.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            Accept
          </button>
          <button
            class="flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white transition-colors hover:bg-white/20"
            title="Dismiss"
            @click="decline"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Realtime toast (payment received, doctor joined) -->
    <div
      v-if="toast"
      class="fixed bottom-5 right-5 z-[99] max-w-xs rounded-2xl border border-ink-200 bg-white px-4 py-3 shadow-xl"
    >
      <div class="flex items-start gap-2.5">
        <span class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M6 9a6 6 0 1112 0c0 5 2 6 2 6H4s2-1 2-6M10 19a2 2 0 004 0" stroke-linecap="round" />
          </svg>
        </span>
        <p class="text-[12.5px] leading-relaxed text-ink-700">{{ toast }}</p>
        <button class="ml-1 text-ink-400 transition-colors hover:text-ink-700" aria-label="Dismiss" @click="toast = null">
          <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
          </svg>
        </button>
      </div>
    </div>
  </Teleport>
</template>
