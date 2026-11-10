<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useUiStore } from '@/stores/ui';

const { t } = useI18n();
const ui = useUiStore();

const form = ref({ name: '', email: '', topic: 'general', message: '' });
const sent = ref(false);

function submit() {
  // No mail transport is configured in this deployment; acknowledge locally.
  sent.value = true;
  ui.notify('Message recorded locally — no mail transport is configured yet.', 'info');
  form.value = { name: '', email: '', topic: 'general', message: '' };
}
</script>

<template>
  <div class="container-page max-w-4xl py-16">
    <h1 v-reveal class="section-title">{{ t('footer.contact') }}</h1>

    <div class="mt-8 grid gap-8 lg:grid-cols-2">
      <div v-reveal:1 class="space-y-5">
        <div class="card card-pad transition-shadow duration-300 hover:shadow-card">
          <h2 class="font-semibold">{{ t('trust.emergencyTitle') }}</h2>
          <p class="muted mt-2 leading-relaxed">{{ t('trust.emergencyBody') }}</p>
        </div>
        <div class="card card-pad">
          <h2 class="font-semibold">{{ t('footer.contact') }}</h2>
          <p class="muted mt-2 leading-relaxed">
            A verified contact address will be published here once it is confirmed. Until then, use the form — it is
            recorded locally in this deployment.
          </p>
          <ul class="mt-3 space-y-1.5 text-sm text-ink-600">
            <li>{{ t('legal.privacy') }} — <RouterLink class="text-brand-700 hover:underline" to="/privacy">/privacy</RouterLink></li>
            <li>{{ t('legal.terms') }} — <RouterLink class="text-brand-700 hover:underline" to="/terms">/terms</RouterLink></li>
            <li>{{ t('legal.medical') }} — <RouterLink class="text-brand-700 hover:underline" to="/medical-disclaimer">/medical-disclaimer</RouterLink></li>
          </ul>
        </div>
      </div>

      <form v-reveal:2 class="card card-pad space-y-4" @submit.prevent="submit">
        <div>
          <label class="label" for="c-name">{{ t('auth.name') }}</label>
          <input id="c-name" v-model="form.name" class="input" required />
        </div>
        <div>
          <label class="label" for="c-email">{{ t('auth.email') }}</label>
          <input id="c-email" v-model="form.email" class="input" type="email" required />
        </div>
        <div>
          <label class="label" for="c-topic">{{ t('common.filter') }}</label>
          <select id="c-topic" v-model="form.topic" class="input">
            <option value="general">General</option>
            <option value="privacy">{{ t('legal.privacy') }}</option>
            <option value="safety">{{ t('nav.trust') }}</option>
          </select>
        </div>
        <div>
          <label class="label" for="c-message">{{ t('common.details') }}</label>
          <textarea id="c-message" v-model="form.message" class="input min-h-28" required />
        </div>

        <p v-if="sent" class="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          Thank you — your message was recorded.
        </p>

        <button class="btn-primary w-full" type="submit">{{ t('common.save') }}</button>
      </form>
    </div>
  </div>
</template>
