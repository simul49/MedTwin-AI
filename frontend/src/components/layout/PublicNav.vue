<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { SUPPORTED_LOCALES, type LocaleCode } from '@/i18n';
import { useUiStore } from '@/stores/ui';

const { t } = useI18n();
const route = useRoute();
const ui = useUiStore();

const open = ref(false);
const langOpen = ref(false);
const portalOpen = ref(false);
const scrolled = ref(false);

const links = computed(() => [
  { to: '/about', label: t('nav.about') },
  { to: '/solutions', label: t('nav.solutions') },
  { to: '/how-it-works', label: t('nav.howItWorks') },
  { to: '/research', label: t('nav.research') },
  { to: '/trust-safety', label: t('nav.trust') },
]);

const isActive = (to: string) => route.path === to || route.path.startsWith(`${to}/`);

watch(() => route.fullPath, () => {
  open.value = false;
  langOpen.value = false;
  portalOpen.value = false;
});

function onScroll() {
  scrolled.value = window.scrollY > 8;
}

onMounted(() => {
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
});

onUnmounted(() => window.removeEventListener('scroll', onScroll));

function pickLocale(code: LocaleCode) {
  ui.setLocale(code);
  langOpen.value = false;
}
</script>

<template>
  <header
    class="sticky top-0 z-40 border-b transition-all duration-300"
    :class="scrolled ? 'border-ink-200 bg-white/95 shadow-card backdrop-blur-md' : 'border-transparent bg-white/70 backdrop-blur'"
  >
    <div class="container-page flex h-16 items-center justify-between gap-4">
      <!-- Left: brand (returns to homepage; no separate Home link) -->
      <RouterLink to="/" class="group flex shrink-0 items-center gap-2" aria-label="MedTwin AI home">
        <span
          class="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-sm font-bold text-white
                 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3"
        >MT</span>
        <span class="text-lg font-extrabold tracking-tight text-brand-700">MedTwin.ai</span>
      </RouterLink>

      <!-- Center: the five primary links, grouped -->
      <nav class="hidden items-center gap-1 lg:flex" :aria-label="t('nav.menu')">
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="relative rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-200
                 after:absolute after:inset-x-3 after:bottom-0.5 after:h-0.5 after:origin-left
                 after:scale-x-0 after:rounded-full after:bg-brand-600 after:transition-transform after:duration-300"
          :class="[
            isActive(link.to)
              ? 'text-brand-700 after:scale-x-100'
              : 'text-ink-600 hover:bg-ink-100 hover:text-ink-900',
          ]"
          :aria-current="isActive(link.to) ? 'page' : undefined"
        >
          {{ link.label }}
        </RouterLink>
      </nav>

      <!-- Right: language + portal selectors -->
      <div class="flex items-center gap-2">
        <div class="relative">
          <button
            class="btn-secondary px-3 py-2 text-xs"
            :aria-expanded="langOpen"
            aria-haspopup="true"
            @click="langOpen = !langOpen"
          >
            {{ ui.locale === 'zh' ? '中文' : 'EN' }}
            <span aria-hidden="true" class="transition-transform duration-200" :class="langOpen ? 'rotate-180' : ''">▾</span>
          </button>
          <Transition name="pop">
            <div
              v-if="langOpen"
              class="absolute right-0 mt-2 w-28 overflow-hidden rounded-xl border border-ink-200 bg-white shadow-card"
            >
              <button
                v-for="option in SUPPORTED_LOCALES"
                :key="option.code"
                class="block w-full px-3 py-2 text-left text-sm transition-colors hover:bg-ink-100"
                :class="ui.locale === option.code ? 'font-semibold text-brand-700' : 'text-ink-700'"
                @click="pickLocale(option.code)"
              >
                {{ option.label }}
              </button>
            </div>
          </Transition>
        </div>

        <div class="relative">
          <button class="btn-primary px-3 py-2 text-xs" :aria-expanded="portalOpen" @click="portalOpen = !portalOpen">
            {{ t('nav.portal') }}
            <span aria-hidden="true" class="transition-transform duration-200" :class="portalOpen ? 'rotate-180' : ''">▾</span>
          </button>
          <Transition name="pop">
            <div
              v-if="portalOpen"
              class="absolute right-0 mt-2 w-44 overflow-hidden rounded-xl border border-ink-200 bg-white shadow-card"
            >
              <RouterLink to="/login?portal=patient" class="block px-3 py-2 text-sm text-ink-700 transition-colors hover:bg-ink-100">
                {{ t('nav.patientPortal') }}
              </RouterLink>
              <RouterLink to="/login?portal=doctor" class="block px-3 py-2 text-sm text-ink-700 transition-colors hover:bg-ink-100">
                {{ t('nav.doctorPortal') }}
              </RouterLink>
              <RouterLink to="/login?portal=admin" class="block px-3 py-2 text-sm text-ink-700 transition-colors hover:bg-ink-100">
                {{ t('nav.adminPortal') }}
              </RouterLink>
            </div>
          </Transition>
        </div>

        <button
          class="btn-ghost flex h-9 w-9 flex-col items-center justify-center gap-1 px-0 lg:hidden"
          :aria-expanded="open"
          :aria-label="t('nav.menu')"
          @click="open = !open"
        >
          <span class="h-0.5 w-5 rounded bg-ink-700 transition-all duration-300" :class="open ? 'translate-y-[3px] rotate-45' : ''" />
          <span class="h-0.5 w-5 rounded bg-ink-700 transition-all duration-300" :class="open ? '-translate-y-[3px] -rotate-45' : ''" />
        </button>
      </div>
    </div>

    <!-- Mobile menu keeps language and portal reachable -->
    <Transition name="pop">
      <nav v-if="open" class="border-t border-ink-200 bg-white lg:hidden" :aria-label="t('nav.menu')">
        <div class="container-page flex flex-col py-2">
          <RouterLink
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="rounded-lg px-3 py-2.5 text-sm font-medium"
            :class="isActive(link.to) ? 'bg-brand-50 text-brand-700' : 'text-ink-700'"
          >
            {{ link.label }}
          </RouterLink>
          <div class="mt-2 flex gap-2 border-t border-ink-100 pt-3">
            <button
              v-for="option in SUPPORTED_LOCALES"
              :key="option.code"
              class="chip"
              :class="ui.locale === option.code ? 'bg-brand-600 text-white' : 'bg-ink-100 text-ink-700'"
              @click="pickLocale(option.code)"
            >
              {{ option.label }}
            </button>
          </div>
          <div class="mt-2 flex gap-2">
            <RouterLink to="/login?portal=patient" class="btn-secondary flex-1 text-xs">{{ t('nav.patientPortal') }}</RouterLink>
            <RouterLink to="/login?portal=doctor" class="btn-secondary flex-1 text-xs">{{ t('nav.doctorPortal') }}</RouterLink>
            <RouterLink to="/login?portal=admin" class="btn-secondary flex-1 text-xs">{{ t('nav.adminPortal') }}</RouterLink>
          </div>
        </div>
      </nav>
    </Transition>
  </header>
</template>
