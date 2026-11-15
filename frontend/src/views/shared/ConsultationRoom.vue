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
const ended = computed(() => status.value === 'COMPLETED');
const reconnecting = ref(false);
const micOn = ref(true);
const camOn = ref(true);
const sharing = ref(false);
const error = ref<string | null>(null);
const localVideo = ref<HTMLVideoElement | null>(null);
const remoteVideo = ref<HTMLVideoElement | null>(null);
const prescription = ref('');
const saving = ref(false);
const elapsed = ref(0);
const quality = ref<'good' | 'fair' | 'poor'>('good');
const turnEnabled = ref(false);
const peerOnline = ref(false);

const isDoctor = computed(() => auth.isDoctor);
const counterpartId = computed(() => {
  if (!consultation.value) return '';
  return isDoctor.value ? consultation.value.patient?.id ?? '' : consultation.value.doctor?.id ?? '';
});
const qualityTone = computed(() =>
  quality.value === 'good' ? 'bg-brand-500' : quality.value === 'fair' ? 'bg-amber-400' : 'bg-rose-500',
);
// Perfect negotiation: the "polite" peer rolls back on offer collisions.
const polite = computed(() => (auth.user?.id ?? '') > counterpartId.value);

// --- WebRTC state ------------------------------------------------------------
let pc: RTCPeerConnection | null = null;
let localStream: MediaStream | null = null;
let cameraTrack: MediaStreamTrack | null = null;
let screenStream: MediaStream | null = null;
let iceServers: RTCIceServer[] = [{ urls: 'stun:stun.l.google.com:19302' }];
// ok = camera+mic live · audio-only = no camera found · none = no media at all
const mediaState = ref<'ok' | 'audio-only' | 'none'>('ok');
const hasLocalVideo = computed(() => mediaState.value === 'ok');
let makingOffer = false;
let ignoreOffer = false;
let iceRestartAttempts = 0;
let timerInterval: number | undefined;
let statsInterval: number | undefined;
let statsFailures = 0;
let offRoom: (() => void) | null = null;
let offSignal: (() => void) | null = null;
let offRoomUsers: (() => void) | null = null;
let offPeerLeft: (() => void) | null = null;
const MAX_ICE_RESTARTS = 4;

async function loadIceConfig() {
  try {
    const config = await consultations.ice();
    if (config.iceServers?.length) iceServers = config.iceServers;
    turnEnabled.value = config.turnEnabled;
  } catch {
    // fall back to public STUN
  }
}

function mediaErrorMessage(err: unknown): string {
  const name = (err as DOMException)?.name ?? '';
  if (name === 'NotAllowedError' || name === 'SecurityError') {
    return 'Camera/microphone access was blocked. Click the camera icon in your browser address bar, allow access for this site, then rejoin the room.';
  }
  if (name === 'NotFoundError' || name === 'OverconstrainedError') {
    return 'No camera was found on this device. You can still take part — the call continues in audio-only mode when a microphone is available.';
  }
  if (name === 'NotReadableError') {
    return 'Your camera is in use by another application (Zoom, Teams, FaceTime…). Close it, then rejoin the room.';
  }
  if (!navigator.mediaDevices?.getUserMedia) {
    return 'Video calls need a secure connection — open the app via https:// or http://localhost. Camera access is blocked over plain http from other devices.';
  }
  return 'Camera or microphone unavailable.';
}

async function ensureLocalStream() {
  if (localStream) return localStream;
  if (!navigator.mediaDevices?.getUserMedia) {
    mediaState.value = 'none';
    throw new Error('getUserMedia unavailable (insecure context)');
  }
  try {
    localStream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: { echoCancellation: true, noiseSuppression: true },
    });
    mediaState.value = 'ok';
  } catch (err) {
    // Degrade gracefully: a missing/blocked camera must not kill the call.
    try {
      localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaState.value = 'audio-only';
    } catch {
      mediaState.value = 'none';
      throw err;
    }
  }
  cameraTrack = localStream.getVideoTracks()[0] ?? null;
  if (localVideo.value && cameraTrack) localVideo.value.srcObject = localStream;
  return localStream;
}

function createPeer(): RTCPeerConnection {
  const peer = new RTCPeerConnection({ iceServers });
  localStream?.getTracks().forEach((track) => peer.addTrack(track, localStream!));

  // Renegotiate whenever tracks/transceivers change (perfect negotiation).
  peer.onnegotiationneeded = async () => {
    try {
      makingOffer = true;
      await peer.setLocalDescription();
      if (counterpartId.value) {
        realtime.signal(room.value, counterpartId.value, {
          sdp: { type: peer.localDescription?.type, sdp: peer.localDescription?.sdp },
        });
      }
    } catch {
      // retried on the next transceiver change
    } finally {
      makingOffer = false;
    }
  };

  peer.onicecandidate = (event) => {
    if (event.candidate && counterpartId.value) {
      realtime.signal(room.value, counterpartId.value, { candidate: event.candidate.toJSON() });
    }
  };

  peer.ontrack = (event) => {
    if (remoteVideo.value) remoteVideo.value.srcObject = event.streams[0];
  };

  peer.oniceconnectionstatechange = () => handleIceState(peer);
  peer.onconnectionstatechange = () => {
    if (peer.connectionState === 'connected' && !live.value) markLive();
  };
  return peer;
}

function handleIceState(peer: RTCPeerConnection) {
  const state = peer.iceConnectionState;
  if (state === 'connected' || state === 'completed') {
    live.value = true;
    reconnecting.value = false;
    iceRestartAttempts = 0;
  } else if (state === 'disconnected') {
    reconnecting.value = true;
    // minor hiccups heal themselves; restart only if it persists
    window.setTimeout(() => {
      if (pc?.iceConnectionState === 'disconnected') void restartIce();
    }, 4000);
  } else if (state === 'failed') {
    void restartIce();
  } else if (state === 'closed') {
    live.value = false;
  }
}

function markLive() {
  live.value = true;
  reconnecting.value = false;
  if (!timerInterval) {
    timerInterval = window.setInterval(() => (elapsed.value += 1), 1000);
    statsInterval = window.setInterval(pollQuality, 5000);
  }
}

async function restartIce() {
  if (!pc || iceRestartAttempts >= MAX_ICE_RESTARTS) return;
  iceRestartAttempts += 1;
  reconnecting.value = true;
  try {
    const offer = await pc.createOffer({ iceRestart: true });
    await pc.setLocalDescription(offer);
    if (counterpartId.value) {
      realtime.signal(room.value, counterpartId.value, {
        sdp: { type: pc.localDescription?.type, sdp: pc.localDescription?.sdp },
      });
    }
  } catch {
    // a peer-left event will clean up if the other side is really gone
  }
}

/** Watch the RTT to grade the call quality for the user. */
async function pollQuality() {
  if (!pc || !live.value) return;
  try {
    const stats = await pc.getStats();
    let rtt: number | null = null;
    stats.forEach((report) => {
      const pair = report as { type?: string; state?: string; currentRoundTripTime?: number };
      if (pair.type === 'candidate-pair' && pair.state === 'succeeded' && pair.currentRoundTripTime != null) {
        rtt = pair.currentRoundTripTime;
      }
    });
    statsFailures = 0;
    if (rtt != null) quality.value = rtt < 0.15 ? 'good' : rtt < 0.35 ? 'fair' : 'poor';
  } catch {
    statsFailures += 1;
    if (statsFailures > 3) quality.value = 'poor';
  }
}

async function handleSignal(payload: Record<string, unknown>) {
  const from = String(payload.from ?? '');
  const data = payload.data as
    | { sdp?: { type: string; sdp: string }; candidate?: RTCIceCandidateInit }
    | undefined;
  if (!data) return;
  try {
    await ensureLocalStream();
    if (!pc) pc = createPeer();

    if (data.sdp) {
      const offerCollision =
        data.sdp.type === 'offer' && (makingOffer || pc.signalingState !== 'stable');
      ignoreOffer = !polite.value && offerCollision;
      if (ignoreOffer) return;

      await pc.setRemoteDescription(new RTCSessionDescription(data.sdp as RTCSessionDescriptionInit));

      if (data.sdp.type === 'offer') {
        await pc.setLocalDescription();
        realtime.signal(room.value, from, {
          sdp: { type: pc.localDescription?.type, sdp: pc.localDescription?.sdp },
        });
      }
    } else if (data.candidate) {
      try {
        await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
      } catch (err) {
        if (!ignoreOffer) throw err;
      }
    }
  } catch (err) {
    if (mediaState.value === 'none') {
      error.value = mediaErrorMessage(err);
    }
    // other failures are transient signalling races — perfect negotiation recovers
  }
}

/** Called when the room roster shows the counterpart present. */
async function onRoomUsers(users: string[]) {
  const other = users.find((u) => u !== auth.user?.id);
  peerOnline.value = Boolean(other);
  if (other && !pc) {
    try {
      await ensureLocalStream();
      pc = createPeer(); // onnegotiationneeded sends the offer
    } catch (err) {
      error.value = mediaErrorMessage(err);
    }
  }
}

// --- media controls -----------------------------------------------------------
async function toggleMic() {
  micOn.value = !micOn.value;
  localStream?.getAudioTracks().forEach((t) => (t.enabled = micOn.value));
}

async function toggleCam() {
  camOn.value = !camOn.value;
  localStream?.getVideoTracks().forEach((t) => (t.enabled = camOn.value));
}

/** Replace the outgoing camera track with the screen; restores on stop. */
async function toggleShare() {
  try {
    if (sharing.value) {
      screenStream?.getTracks().forEach((t) => t.stop());
      screenStream = null;
      sharing.value = false;
      if (cameraTrack && pc) {
        const sender = pc.getSenders().find((s) => s.track?.kind === 'video');
        await sender?.replaceTrack(cameraTrack);
        cameraTrack.enabled = true;
        if (localVideo.value) localVideo.value.srcObject = localStream;
      }
      return;
    }
    screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
    const screenTrack = screenStream.getVideoTracks()[0];
    if (pc) {
      const sender = pc.getSenders().find((s) => s.track?.kind === 'video');
      await sender?.replaceTrack(screenTrack);
    }
    if (cameraTrack) cameraTrack.enabled = false;
    sharing.value = true;
    if (localVideo.value && screenStream) localVideo.value.srcObject = screenStream;
    screenTrack.onended = () => {
      if (sharing.value) void toggleShare();
    };
  } catch {
    // user dismissed the picker — keep the camera view
  }
}

function formatElapsed(total: number): string {
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const mm = String(m).padStart(2, '0');
  const ss = String(s).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
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
  screenStream?.getTracks().forEach((t) => t.stop());
  screenStream = null;
  localStream?.getTracks().forEach((t) => t.stop());
  localStream = null;
  cameraTrack = null;
  if (timerInterval) window.clearInterval(timerInterval);
  if (statsInterval) window.clearInterval(statsInterval);
  timerInterval = undefined;
  statsInterval = undefined;
  offRoomUsers?.();
  offSignal?.();
  offPeerLeft?.();
  offRoom?.();
  if (room.value) realtime.leave(room.value);
}

onMounted(async () => {
  error.value = null;
  try {
    // Completed consultations open in summary mode — prescription, payment
    // receipt and timing; no room join, no camera.
    consultation.value = await consultations.detail(props.id);
    status.value = consultation.value.status;
    if (consultation.value.prescriptionNote) prescription.value = consultation.value.prescriptionNote;
    if (consultation.value.status === 'COMPLETED') return;

    await loadIceConfig();
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
      void onRoomUsers((payload.users as string[]) ?? []);
    });
    offSignal = realtime.on('signal', handleSignal);
    offPeerLeft = realtime.on('peer-left', (payload) => {
      const userId = String(payload.userId ?? '');
      if (userId && userId !== auth.user?.id) {
        live.value = false;
        reconnecting.value = false;
        peerOnline.value = false;
        if (remoteVideo.value) remoteVideo.value.srcObject = null;
        pc?.close();
        pc = null;
      }
    });

    realtime.connect();
    realtime.join(room.value);

    // Start the local camera right away so users see their own preview while
    // waiting — a blocked/missing camera surfaces here, not mid-negotiation.
    try {
      await ensureLocalStream();
    } catch (err) {
      error.value = mediaErrorMessage(err);
    }
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
          <span v-if="live"> · {{ formatElapsed(elapsed) }}</span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span class="chip bg-brand-50 font-semibold text-brand-700">
          <span class="h-1.5 w-1.5 rounded-full" :class="live ? qualityTone : 'bg-ink-300'" />
          {{ ended ? 'Consultation ended' : live ? `Connected · ${quality} quality` : reconnecting ? 'Reconnecting…' : peerOnline ? 'Peer in room' : 'Waiting for the other participant' }}
        </span>
        <button class="btn-danger px-3 py-1.5 text-xs" @click="endCall">{{ ended ? 'Back to consultations' : 'Leave room' }}</button>
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
          <p class="text-[14px] font-semibold text-white/80">{{ ended ? 'Consultation ended' : reconnecting ? 'Reconnecting…' : 'Waiting room' }}</p>
          <p class="max-w-xs text-[12px] text-white/50">
            {{ ended
              ? 'Read the advice & prescription in the summary panel — it stays available here.'
              : reconnecting
              ? 'The connection dropped — restoring the video call automatically.'
              : 'The video call starts automatically when both participants are in the room.' }}
          </p>
        </div>
        <span
          v-if="live"
          class="absolute left-3 top-3 rounded-full bg-black/50 px-2.5 py-1 text-[11px] font-bold tabular-nums text-white"
        >{{ formatElapsed(elapsed) }}</span>
        <span
          v-if="sharing"
          class="absolute right-3 top-3 rounded-full bg-brand-600 px-2.5 py-1 text-[11px] font-bold text-white"
        >Sharing screen</span>
        <!-- local preview -->
        <video
          v-show="hasLocalVideo"
          ref="localVideo"
          autoplay
          playsinline
          muted
          class="absolute bottom-14 right-3 h-28 w-44 rounded-xl border border-white/20 object-cover shadow-lg"
        />
        <span
          v-if="mediaState === 'audio-only'"
          class="absolute bottom-14 right-3 rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-[11px] font-semibold text-white/80"
        >
          Audio-only mode — no camera available
        </span>
        <!-- controls -->
        <div v-if="!ended" class="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-2">
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
          <button
            class="flex h-10 w-10 items-center justify-center rounded-full text-white shadow-lg transition-colors"
            :class="sharing ? 'bg-brand-600' : 'bg-white/20 hover:bg-white/30'"
            title="Share your screen"
            @click="toggleShare"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path d="M3 5h18v11H3zM8 21h8M12 16v5M12 12V8m0 0l-2.5 2.5M12 8l2.5 2.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          <button
            class="flex h-10 items-center justify-center gap-1.5 rounded-full bg-rose-600 px-4 text-[12px] font-bold text-white shadow-lg transition-colors hover:bg-rose-500"
            title="End the call"
            @click="endCall"
          >
            End
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
          Encrypted peer-to-peer call
          <span v-if="turnEnabled">· relayed via your TURN server when needed</span>
          · nothing is recorded by the platform.
        </div>
      </div>
    </div>
  </div>
</template>
