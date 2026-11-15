<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { consultations } from '@/api/endpoints';
import { useRealtime } from '@/composables/useRealtime';
import type { Consultation } from '@/api/types';

const props = defineProps<{ id: string }>();
const router = useRouter();
const auth = useAuthStore();
const realtime = useRealtime();

const consultation = ref<Consultation | null>(null);
const room = ref('');
const status = ref<string>('');
const live = ref(false);
const micOn = ref(true);
const camOn = ref(true);
const error = ref<string | null>(null);
const localVideo = ref<HTMLVideoElement | null>(null);
const remoteVideo = ref<HTMLVideoElement | null>(null);
const prescription = ref('');
const saving = ref(false);

const isDoctor = computed(() => auth.isDoctor);
const counterpartId = computed(() => {
  if (!consultation.value) return '';
  return isDoctor.value ? consultation.value.patient?.id ?? '' : consultation.value.doctor?.id ?? '';
});

// --- WebRTC state ------------------------------------------------------------
let pc: RTCPeerConnection | null = null;
let localStream: MediaStream | null = null;
let offRoom: (() => void) | null = null;
let offSignal: (() => void) | null = null;
let offRoomUsers: (() => void) | null = null;
let offPeerLeft: (() => void) | null = null;

function pcConfig(): RTCConfiguration {
  return { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }, { urls: 'stun:stun1.l.google.com:19302' }] };
}

async function ensureLocalStream() {
  if (localStream) return localStream;
  localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  if (localVideo.value) localVideo.value.srcObject = localStream;
  return localStream;
}

function createPeer(): RTCPeerConnection {
  const peer = new RTCPeerConnection(pcConfig());
  localStream?.getTracks().forEach((track) => peer.addTrack(track, localStream!));
  peer.onicecandidate = (event) => {
    if (event.candidate && counterpartId.value) {
      realtime.signal(room.value, counterpartId.value, { candidate: event.candidate.toJSON() });
    }
  };
  peer.ontrack = (event) => {
    if (remoteVideo.value) remoteVideo.value.srcObject = event.streams[0];
    live.value = true;
  };
  return peer;
}

/** Deterministic initiator: the lexicographically smaller userId sends the offer. */
function shouldInitiate(otherId: string): boolean {
  return (auth.user?.id ?? '') < otherId;
}

async function startCall(otherId: string) {
  try {
    await ensureLocalStream();
    pc?.close();
    pc = createPeer();
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    realtime.signal(room.value, otherId, { sdp: { type: offer.type, sdp: offer.sdp } });
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Camera or microphone unavailable.';
  }
}

async function handleSignal(payload: Record<string, unknown>) {
  const from = String(payload.from ?? '');
  const data = payload.data as { sdp?: { type: string; sdp: string }; candidate?: RTCIceCandidateInit } | undefined;
  if (!data) return;
  try {
    await ensureLocalStream();
    pc?.close();
    pc = pc && pc.connectionState !== 'closed' ? pc : createPeer();
    if (data.sdp?.type === 'offer') {
      await pc.setRemoteDescription(new RTCSessionDescription(data.sdp as RTCSessionDescriptionInit));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      realtime.signal(room.value, from, { sdp: { type: answer.type, sdp: answer.sdp } });
    } else if (data.sdp?.type === 'answer') {
      await pc.setRemoteDescription(new RTCSessionDescription(data.sdp as RTCSessionDescriptionInit));
    } else if (data.candidate) {
      await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
    }
  } catch {
    // transient signalling race — ICE retries recover
  }
}

async function toggleMic() {
  micOn.value = !micOn.value;
  localStream?.getAudioTracks().forEach((t) => (t.enabled = micOn.value));
}

async function toggleCam() {
  camOn.value = !camOn.value;
  localStream?.getVideoTracks().forEach((t) => (t.enabled = camOn.value));
}

async function endCall() {
  cleanup();
  router.push(isDoctor.value ? '/doctor/consultations' : '/patient/consultations');
}

async function sendPrescription() {
  if (!prescription.value.trim() || !consultation.value) return;
  saving.value = true;
  try {
    consultation.value = await consultations.prescribe(consultation.value.id, prescription.value.trim());
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    saving.value = false;
  }
}

function cleanup() {
  pc?.close();
  pc = null;
  localStream?.getTracks().forEach((t) => t.stop());
  localStream = null;
  offRoomUsers?.();
  offSignal?.();
  offPeerLeft?.();
  offRoom?.();
  if (room.value) realtime.leave(room.value);
}

onMounted(async () => {
  error.value = null;
  try {
    consultation.value = await consultations.join(props.id);
    room.value = String((consultation.value as { room?: string }).room ?? '');
    status.value = consultation.value.status;
    if (consultation.value.prescriptionNote) prescription.value = consultation.value.prescriptionNote;

    offRoom = realtime.on('consultation-update', (payload) => {
      const updated = payload.consultation as Consultation | undefined;
      if (updated && updated.id === consultation.value?.id) {
        consultation.value = { ...consultation.value, ...updated };
        status.value = updated.status;
      }
    });
    offRoomUsers = realtime.on('room-users', (payload) => {
      const users = (payload.users as string[]) ?? [];
      const other = users.find((u) => u !== auth.user?.id);
      if (other && shouldInitiate(other)) void startCall(other);
    });
    offSignal = realtime.on('signal', handleSignal);
    offPeerLeft = realtime.on('peer-left', () => {
      live.value = false;
      if (remoteVideo.value) remoteVideo.value.srcObject = null;
      pc?.close();
      pc = null;
    });

    realtime.connect();
    realtime.join(room.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
});

onUnmounted(cleanup);
</script>

<template>
  <div>
    <header class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="dash-kicker mb-1.5">Video consultation</p>
        <h1 class="text-[24px] font-bold leading-tight tracking-tight text-ink-900">
          {{ isDoctor ? consultation?.patient?.name ?? 'Patient' : consultation?.doctor?.name ?? 'Clinician' }}
        </h1>
        <p class="mt-0.5 text-[12px] text-ink-400">
          Room {{ consultation?.roomCode || '—' }} ·
          <span :class="status === 'LIVE' ? 'font-semibold text-brand-700' : 'text-ink-400'">{{ status }}</span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span class="chip bg-brand-50 font-semibold text-brand-700">
          <span class="h-1.5 w-1.5 rounded-full" :class="live ? 'bg-brand-500' : 'bg-ink-300'" />
          {{ live ? 'Connected' : 'Waiting for the other participant' }}
        </span>
        <button class="btn-danger px-3 py-1.5 text-xs" @click="endCall">Leave room</button>
      </div>
    </header>

    <p v-if="error" class="dash-card mb-4 border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <div class="grid gap-4 lg:grid-cols-[minmax(0,2.2fr)_minmax(0,1fr)]">
      <!-- Video stage -->
      <div class="dash-card relative overflow-hidden bg-ink-900" style="min-height: 24rem">
        <video ref="remoteVideo" autoplay playsinline class="h-full w-full object-cover" />
        <div
          v-if="!live"
          class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-ink-900 text-center"
        >
          <span class="flex h-12 w-12 animate-pulse rounded-full bg-white/10 items-center justify-center">
            <svg class="h-5 w-5 text-white/70" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM4 21a8 8 0 0116 0" stroke-linecap="round" />
            </svg>
          </span>
          <p class="text-[14px] font-semibold text-white/80">Waiting room</p>
          <p class="max-w-xs text-[12px] text-white/50">
            The video call starts automatically when both participants are in the room.
          </p>
        </div>
        <!-- local preview -->
        <video
          ref="localVideo"
          autoplay
          playsinline
          muted
          class="absolute bottom-3 right-3 h-28 w-44 rounded-xl border border-white/20 object-cover shadow-lg"
        />
        <!-- controls -->
        <div class="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-2">
          <button
            class="flex h-10 w-10 items-center justify-center rounded-full text-white shadow-lg transition-colors"
            :class="micOn ? 'bg-white/20 hover:bg-white/30' : 'bg-rose-600'"
            :title="micOn ? 'Mute microphone' : 'Unmute microphone'"
            @click="toggleMic"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path v-if="micOn" d="M12 3a3 3 0 013 3v5a3 3 0 01-6 0V6a3 3 0 013-3zM5 11a7 7 0 0014 0M12 18v3" stroke-linecap="round" />
              <path v-else d="M9 9v2a3 3 0 004.5 2.6M15 11V6a3 3 0 00-5.7-1.3M5 11a7 7 0 0010.6 6M12 18v3M4 4l16 16" stroke-linecap="round" />
            </svg>
          </button>
          <button
            class="flex h-10 w-10 items-center justify-center rounded-full text-white shadow-lg transition-colors"
            :class="camOn ? 'bg-white/20 hover:bg-white/30' : 'bg-rose-600'"
            :title="camOn ? 'Turn camera off' : 'Turn camera on'"
            @click="toggleCam"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path v-if="camOn" d="M3 7h11v10H3zM14 10l6-3v10l-6-3" stroke-linecap="round" stroke-linejoin="round" />
              <path v-else d="M3 7h11v10H3zM14 10l6-3v10l-6-3M3 3l18 18" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Side panel -->
      <div class="space-y-4">
        <div class="dash-card dash-card-pad">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M12 8v5m0 3v.5M12 3a9 9 0 100 18 9 9 0 000-18z" stroke-linecap="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">Consultation summary</p>
              <p class="dash-section-sub mt-0.5">
                Fee {{ consultation?.feeCurrency }} {{ consultation?.feeAmount }} ·
                {{ consultation?.payment?.status === 'PAID' ? `Paid · receipt ${consultation?.payment?.receiptNo}` : 'Unpaid' }}
              </p>
            </div>
          </div>

          <!-- Patient: read the prescription -->
          <div v-if="!isDoctor">
            <div v-if="consultation?.prescriptionNote" class="mt-4 rounded-xl border border-brand-200 bg-brand-50 px-3.5 py-3">
              <p class="text-[11px] font-bold uppercase tracking-wide text-brand-700">Advice & prescription</p>
              <p class="mt-1.5 whitespace-pre-wrap text-[13px] leading-relaxed text-ink-700">{{ consultation.prescriptionNote }}</p>
            </div>
            <p v-else class="mt-4 text-[12px] text-ink-400">
              Your clinician's advice and prescription will appear here after the consultation.
            </p>
          </div>

          <!-- Doctor: issue the prescription -->
          <form v-else class="mt-4 space-y-3" @submit.prevent="sendPrescription">
            <label class="label" for="rx-note">Advice / prescription</label>
            <textarea
              id="rx-note"
              v-model="prescription"
              class="input min-h-32"
              placeholder="Diagnosis summary, medications, dosage and follow-up instructions…"
              :disabled="consultation?.status === 'COMPLETED'"
            />
            <button class="dash-btn w-full" type="submit" :disabled="saving || consultation?.status === 'COMPLETED'">
              {{ consultation?.status === 'COMPLETED' ? 'Sent ✓' : saving ? 'Sending…' : 'Send prescription & finish' }}
            </button>
          </form>
        </div>

        <div class="dash-info">
          This call is peer-to-peer in your browser. Nothing is recorded by the platform.
        </div>
      </div>
    </div>
  </div>
</template>
