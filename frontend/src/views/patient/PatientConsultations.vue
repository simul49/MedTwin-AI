<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { consultations, payments } from '@/api/endpoints';
import { formatDateTime } from '@/composables/useAsync';
import type { Consultation } from '@/api/types';

const route = useRoute();

const items = ref<Consultation[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const success = ref<string | null>(null);

const payFor = ref<Consultation | null>(null);
const card = ref({ cardNumber: '', cardName: '', expiry: '', cvc: '' });
const processing = ref(false);
const payError = ref<string | null>(null);
const receipt = ref<{ receiptNo: string | null; amount: number; currency: string; cardLast4: string | null } | null>(null);

const paid = computed(() => items.value.filter((c) => ['PAID', 'WAITING_ROOM', 'LIVE', 'COMPLETED', 'EXPIRED'].includes(c.status)));
const awaitingPayment = computed(() => items.value.filter((c) => ['SCHEDULED', 'PAYMENT_PENDING'].includes(c.status)));

const STATUS_TONE: Record<string, string> = {
  PAYMENT_PENDING: 'bg-amber-50 text-amber-700',
  SCHEDULED: 'bg-surface-100 text-ink-600',
  PAID: 'bg-brand-50 text-brand-700',
  WAITING_ROOM: 'bg-brand-50 text-brand-700',
  LIVE: 'bg-brand-600 text-white',
  COMPLETED: 'bg-surface-100 text-ink-600',
  CANCELLED: 'bg-rose-50 text-rose-600',
  EXPIRED: 'bg-ink-100 text-ink-500',
};

function openCheckout(item: Consultation) {
  payFor.value = item;
  payError.value = null;
  receipt.value = null;
  card.value = { cardNumber: '', cardName: '', expiry: '', cvc: '' };
}

async function submitPayment() {
  if (!payFor.value) return;
  processing.value = true;
  payError.value = null;
  try {
    const result = await payments.checkout({
      consultationId: payFor.value.id,
      cardNumber: card.value.cardNumber,
      cardName: card.value.cardName,
      expiry: card.value.expiry,
      cvc: card.value.cvc,
    });
    receipt.value = {
      receiptNo: result.receiptNo,
      amount: result.amount,
      currency: result.currency,
      cardLast4: result.cardLast4,
    };
    const idx = items.value.findIndex((c) => c.id === payFor.value!.id);
    if (idx >= 0) items.value[idx] = { ...items.value[idx], ...result.consultation };
    success.value = 'Payment received — you can enter the consultation room.';
    setTimeout(() => (success.value = null), 5000);
  } catch (err) {
    payError.value = err instanceof Error ? err.message : String(err);
  } finally {
    processing.value = false;
  }
}

async function cancelConsultation(item: Consultation) {
  if (!window.confirm('Cancel this consultation request?')) return;
  try {
    const updated = await consultations.cancel(item.id);
    const idx = items.value.findIndex((c) => c.id === item.id);
    if (idx >= 0) items.value[idx] = updated;
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  }
}

async function load() {
  loading.value = true;
  try {
    items.value = (await consultations.list()).results;
    // Arriving from appointments with ?pay=<id> opens checkout right away.
    const payId = route.query.pay as string | undefined;
    if (payId) {
      const target = items.value.find((c) => c.id === payId);
      if (target && ['PAYMENT_PENDING', 'SCHEDULED'].includes(target.status)) openCheckout(target);
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <header class="mb-5">
      <p class="dash-kicker mb-1.5">Paid consultations</p>
      <h1 class="text-[26px] font-bold leading-tight tracking-tight text-ink-900">Talk to your clinician</h1>
      <p class="mt-1 text-[13px] text-ink-500">Pay for a video consultation, get advice and a prescription.</p>
    </header>

    <p v-if="success" class="dash-card mb-4 border border-brand-200 bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-700">{{ success }}</p>
    <p v-if="error" class="dash-card mb-4 border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ error }}</p>

    <div class="dash-card overflow-hidden">
      <div class="flex items-center justify-between border-b border-ink-100 bg-surface-50/60 px-4 py-2.5">
        <p class="text-[12px] font-bold uppercase tracking-wide text-ink-500">Your consultations</p>
        <span class="chip bg-surface-100 text-[10.5px] text-ink-500">{{ items.length }}</span>
      </div>

      <div v-if="loading" class="shimmer h-40 animate-pulse bg-ink-50" />

      <div v-else-if="!items.length" class="flex flex-col items-center px-5 py-12 text-center">
        <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path d="M15 10l4.5-4.5M15 10v-2a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2m4.5-8.5L17 5m2.5 2.5L17 10" stroke-linecap="round" />
          </svg>
        </span>
        <p class="mt-3 text-[13.5px] font-semibold text-ink-700">No consultations yet</p>
        <p class="mt-1 max-w-sm text-[11.5px] text-ink-400">
          Book an appointment first — once it is confirmed you can pay for a video consultation and talk to your doctor face to face.
        </p>
        <RouterLink to="/patient/appointments" class="dash-btn mt-4 px-4 py-2 text-xs">Go to appointments</RouterLink>
      </div>

      <ul v-else class="divide-y divide-ink-100">
        <li v-for="item in items" :key="item.id" class="flex flex-wrap items-center gap-3 px-4 py-3 transition-colors hover:bg-surface-50/60">
          <span
            class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[10.5px] font-bold text-white shadow-card"
            :style="{ backgroundColor: item.doctor?.avatarColor ?? '#0A2A63' }"
          >
            {{ item.doctor?.name?.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase() || '—' }}
          </span>
          <div class="min-w-[150px] flex-1">
            <p class="text-[13.5px] font-semibold text-ink-900">{{ item.doctor?.name ?? 'Clinician' }}</p>
            <p class="text-[11px] text-ink-400">
              {{ item.feeCurrency }} {{ item.feeAmount }} · {{ formatDateTime(item.createdAt, 'en') }}
              <span v-if="item.payment?.receiptNo">· receipt {{ item.payment.receiptNo }}</span>
            </p>
          </div>
          <span class="chip shrink-0 font-semibold" :class="STATUS_TONE[item.status] ?? 'bg-surface-100 text-ink-600'">
            {{ item.status.replaceAll('_', ' ').toLowerCase() }}
          </span>
          <div class="flex shrink-0 items-center gap-2">
            <button v-if="['PAYMENT_PENDING', 'SCHEDULED'].includes(item.status)" class="dash-btn px-3 py-1.5 text-xs" @click="openCheckout(item)">
              Pay {{ item.feeCurrency }} {{ item.feeAmount }}
            </button>
            <RouterLink
              v-if="['PAID', 'WAITING_ROOM', 'LIVE'].includes(item.status)"
              :to="`/patient/consultations/${item.id}`"
              class="dash-btn px-3 py-1.5 text-xs"
            >
              {{ item.status === 'LIVE' ? 'Join call' : 'Enter room' }} →
            </RouterLink>
            <RouterLink
              v-if="item.status === 'COMPLETED' && item.prescriptionNote"
              :to="`/patient/consultations/${item.id}`"
              class="btn-secondary px-3 py-1.5 text-xs"
            >View prescription</RouterLink>
            <button
              v-if="['PAYMENT_PENDING', 'SCHEDULED'].includes(item.status)"
              class="text-[11px] font-semibold text-rose-600 hover:underline"
              @click="cancelConsultation(item)"
            >Cancel</button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Checkout modal -->
    <div v-if="payFor" class="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/50 p-4" @click.self="payFor = null">
      <div class="dash-card w-full max-w-md overflow-hidden">
        <div class="flex items-center justify-between border-b border-ink-100 bg-surface-50/60 px-5 py-3">
          <div>
            <p class="text-[14px] font-bold text-ink-900">Pay for your consultation</p>
            <p class="text-[11.5px] text-ink-400">{{ payFor.doctor?.name }} · advice & prescription</p>
          </div>
          <button class="rounded-lg p-1.5 text-ink-400 transition-colors hover:bg-surface-100 hover:text-ink-800" @click="payFor = null">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
            </svg>
          </button>
        </div>

        <!-- Receipt view after success -->
        <div v-if="receipt" class="px-5 py-6 text-center">
          <span class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
              <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <p class="mt-3 text-[15px] font-bold text-ink-900">Payment successful</p>
          <p class="mt-1 text-[12px] text-ink-500">
            {{ receipt.currency }} {{ receipt.amount }} charged to card ···· {{ receipt.cardLast4 }}
          </p>
          <p class="mt-1 text-[11px] text-ink-400">Receipt {{ receipt.receiptNo }}</p>
          <button class="dash-btn mt-5 w-full" type="button" @click="payFor = null; payFor = null">
            <RouterLink :to="`/patient/consultations/${payFor.id}`" class="text-white">Enter consultation room →</RouterLink>
          </button>
        </div>

        <!-- Card form -->
        <form v-else class="space-y-4 px-5 py-5" @submit.prevent="submitPayment">
          <div class="flex items-center justify-between rounded-xl border border-ink-100 bg-surface-50 px-3.5 py-2.5">
            <span class="text-[12px] font-semibold text-ink-600">Consultation fee</span>
            <span class="text-[16px] font-extrabold text-ink-900">{{ payFor.feeCurrency }} {{ payFor.feeAmount }}</span>
          </div>
          <div>
            <label class="label" for="card-number">Card number</label>
            <input id="card-number" v-model="card.cardNumber" class="input" inputmode="numeric" placeholder="4242 4242 4242 4242" required />
          </div>
          <div>
            <label class="label" for="card-name">Cardholder name</label>
            <input id="card-name" v-model="card.cardName" class="input" placeholder="As printed on the card" required />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label" for="card-expiry">Expiry (MM/YY)</label>
              <input id="card-expiry" v-model="card.expiry" class="input" placeholder="12/28" required />
            </div>
            <div>
              <label class="label" for="card-cvc">Security code</label>
              <input id="card-cvc" v-model="card.cvc" class="input" inputmode="numeric" placeholder="123" required />
            </div>
          </div>
          <p v-if="payError" class="rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-[12px] text-rose-700">{{ payError }}</p>
          <button class="dash-btn w-full" type="submit" :disabled="processing">
            {{ processing ? 'Processing payment…' : `Pay ${payFor.feeCurrency} ${payFor.feeAmount}` }}
          </button>
          <p class="text-center text-[10.5px] text-ink-400">
            Demo gateway — no real charge. Test success with 4242 4242 4242 4242, decline with any valid card ending 0002.
          </p>
        </form>
      </div>
    </div>
  </div>
</template>
