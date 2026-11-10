import type { Directive } from 'vue';

/**
 * `v-reveal` — fade/slide elements in as they enter the viewport.
 * Optional stagger delay:  `v-reveal:2`  → 120ms × 2.
 * Respects `prefers-reduced-motion` (elements are shown immediately).
 */
const observer =
  typeof IntersectionObserver !== 'undefined'
    ? new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              entry.target.classList.add('reveal-visible');
              observer?.unobserve(entry.target);
            }
          }
        },
        { threshold: 0.12, rootMargin: '0px 0px -40px 0px' },
      )
    : null;

export const reveal: Directive<HTMLElement, number | undefined> = {
  mounted(el, binding) {
    const step = typeof binding.value === 'number' ? binding.value : null;
    if (step !== null) el.style.transitionDelay = `${Math.min(step * 90, 600)}ms`;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || !observer) {
      el.classList.add('reveal-visible');
      return;
    }
    el.classList.add('reveal');
    observer.observe(el);
  },
  unmounted(el) {
    observer?.unobserve(el);
    el.style.transitionDelay = '';
  },
};
