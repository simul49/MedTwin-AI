<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { patient } from '@/api/endpoints';
import { formatBytes, formatDateTime } from '@/composables/useAsync';
import type { DocumentRecord } from '@/api/types';

const { t } = useI18n();
const router = useRouter();

const documents = ref<DocumentRecord[]>([]);
const selected = ref<DocumentRecord | null>(null);
const loading = ref(false);
const uploading = ref(false);
const dragging = ref(false);
const error = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const category = ref('OTHER');
const attachedMsg = ref('');

function askAi() {
  if (!selected.value) return;
  router.push({
    path: '/patient/assistant',
    query: {
      q: `What does my document "${selected.value.name}" say? Summarize the key medical information in it.`,
    },
  });
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    documents.value = (await patient.documents()).results;
    if (!selected.value && documents.value.length) selected.value = await patient.document(documents.value[0].id);
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    loading.value = false;
  }
}

async function uploadFiles(files: FileList | File[] | null) {
  const file = files?.[0];
  if (!file) return;
  uploading.value = true;
  error.value = null;
  try {
    await patient.uploadDocument(file, category.value);
    if (fileInput.value) fileInput.value.value = '';
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
  } finally {
    uploading.value = false;
  }
}

function onDrop(event: DragEvent) {
  dragging.value = false;
  void uploadFiles(event.dataTransfer?.files ?? null);
}

function onPick(event: Event) {
  void uploadFiles((event.target as HTMLInputElement).files);
}

async function open(document: DocumentRecord) {
  selected.value = await patient.document(document.id);
}

async function review(extractionId: string, status: string, value?: string) {
  if (!selected.value) return;
  await patient.reviewExtraction(selected.value.id, extractionId, status, value);
  selected.value = await patient.document(selected.value.id);
  await load();
}

async function attachAll() {
  if (!selected.value?.extractions) return;
  const pending = selected.value.extractions.filter(
    (item) => item.reviewStatus === 'PENDING' || item.reviewStatus === 'NEEDS_REVIEW',
  ).length;
  for (const item of selected.value.extractions) {
    if (item.reviewStatus === 'PENDING' || item.reviewStatus === 'NEEDS_REVIEW') {
      await patient.reviewExtraction(selected.value.id, item.id, 'CONFIRMED');
    }
  }
  selected.value = await patient.document(selected.value.id);
  await load();
  if (pending > 0) {
    attachedMsg.value = `Added ${pending} value${pending === 1 ? '' : 's'} to your Digital Twin records — see them under Records.`;
  }
}

async function remove(document: DocumentRecord) {
  if (!window.confirm(t('common.confirm'))) return;
  await patient.deleteDocument(document.id);
  selected.value = null;
  await load();
}

function download(document: DocumentRecord) {
  window.open(`/api/v1/patient/documents/${document.id}/file/`, '_blank');
}

const statusText = (status: string) =>
  status === 'PROCESSED' ? 'Extraction successful' : status === 'FAILED' ? 'Extraction failed' : 'Processing text extraction…';

const statusChip = (status: string) =>
  status === 'PROCESSED' ? 'bg-brand-50 text-brand-700' : status === 'FAILED' ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700';

const reviewChip = (status: string) =>
  status === 'CONFIRMED' ? 'bg-brand-50 text-brand-700'
    : status === 'CORRECTED' ? 'bg-sky-50 text-sky-700'
    : status === 'REJECTED' ? 'bg-rose-50 text-rose-700'
    : 'bg-amber-50 text-amber-700';

const fileIcon = (name: string) =>
  name.toLowerCase().endsWith('.pdf') ? 'M6 2h8l4 4v16H6zM14 2v5h5M9 13h6M9 17h6'
    : name.toLowerCase().match(/\.(png|jpe?g|gif|webp)$/) ? 'M3 5h18v14H3zM3 15l5-5 4 4 3-3 6 6'
    : 'M6 2h8l4 4v16H6zM14 2v5h5';

const pendingCount = () =>
  selected.value?.extractions?.filter((i) => i.reviewStatus === 'PENDING' || i.reviewStatus === 'NEEDS_REVIEW').length ?? 0;

onMounted(load);
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="dash-kicker mb-2">Records &amp; evidence</p>
        <h1 class="text-[28px] font-bold leading-tight tracking-tight text-ink-900">Upload Medical Document</h1>
        <p class="mt-2 text-[14px] text-ink-500">Add a report, prescription or image. Extracted fields always need your review.</p>
      </div>
      <label class="flex items-center gap-2 text-[12px] font-semibold text-ink-500">
        Document category
        <select v-model="category" class="input w-40 text-xs" aria-label="Document category">
          <option value="OTHER">Other</option>
          <option value="LAB">Lab report</option>
          <option value="IMAGING">Imaging</option>
          <option value="PRESCRIPTION">Prescription</option>
          <option value="LETTER">Letter</option>
        </select>
      </label>
    </div>

    <div class="grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,0.9fr)]">
      <div class="space-y-4">
        <!-- Drop zone -->
        <div
          class="dash-card flex min-h-[250px] flex-col items-center justify-center border-2 border-dashed p-6 text-center transition-colors"
          :class="dragging ? 'border-brand-500 bg-brand-50' : 'border-ink-200'"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="onDrop"
        >
          <span class="flex h-16 w-16 items-center justify-center rounded-2xl border border-brand-200 bg-brand-50 shadow-sm">
            <svg class="h-7 w-7 text-brand-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
              <path d="M6 2h8l4 4v16H6zM14 2v5h5M9 14l3-3 3 3M12 11v7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <p class="mt-5 text-[16px] font-bold text-ink-900">Drag &amp; drop your medical documents here</p>
          <label class="mt-2 cursor-pointer rounded-lg px-2 py-1 text-[13px] font-semibold text-brand-700 underline decoration-2 underline-offset-4 hover:bg-brand-50">
            or browse files
            <input class="hidden" type="file" accept=".pdf,.png,.jpg,.jpeg" @change="onPick" />
          </label>
          <p class="mt-3 text-[11px] text-ink-400">PDF, PNG, JPG · max 15 MB</p>
          <p v-if="uploading" class="mt-2 text-[12px] font-semibold text-brand-700">Uploading…</p>
          <p v-if="error" class="mt-2 text-[12px] text-rose-600">{{ error }}</p>
        </div>

        <!-- File table -->
        <div class="dash-card overflow-hidden">
          <div class="flex items-start gap-3 border-b border-ink-100 px-5 py-4">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M6 2h8l4 4v16H6zM14 2v5h5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <div>
              <p class="dash-section-title">
                Uploaded files
                <span class="ml-1.5 rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-bold text-brand-700">{{ documents.length }}</span>
              </p>
              <p class="dash-section-sub mt-0.5">Extraction status and source documents</p>
            </div>
          </div>
          <div v-if="loading" class="h-28 animate-pulse bg-ink-100" />
          <div v-else class="overflow-x-auto">
            <table class="w-full min-w-[620px] border-collapse">
              <thead class="bg-surface-50">
                <tr>
                  <th class="dash-th">Filename</th>
                  <th class="dash-th">Uploaded</th>
                  <th class="dash-th">Size</th>
                  <th class="dash-th">Status</th>
                  <th class="dash-th">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="document in documents"
                  :key="document.id"
                  class="dash-row cursor-pointer"
                  :class="selected?.id === document.id ? 'bg-brand-50/60' : ''"
                  @click="open(document)"
                >
                  <td class="dash-td">
                    <span class="flex items-center gap-2">
                      <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-surface-100 text-ink-500">
                        <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                          <path :d="fileIcon(document.name)" stroke-linecap="round" stroke-linejoin="round" />
                        </svg>
                      </span>
                      <span class="max-w-[240px] truncate font-medium" :class="selected?.id === document.id ? 'text-brand-800' : 'text-ink-700'" :title="document.name">{{ document.name }}</span>
                    </span>
                  </td>
                  <td class="dash-td whitespace-nowrap text-ink-500">{{ formatDateTime(document.createdAt) }}</td>
                  <td class="dash-td whitespace-nowrap">{{ formatBytes(document.sizeBytes) }}</td>
                  <td class="dash-td">
                    <span class="chip whitespace-nowrap" :class="statusChip(document.processingStatus)">
                      {{ statusText(document.processingStatus) }}
                    </span>
                    <p v-if="document.processingStatus === 'FAILED' && document.processingError"
                       class="mt-1 max-w-[220px] text-[10px] leading-snug text-amber-700">
                      {{ document.processingError }}
                    </p>
                  </td>
                  <td class="dash-td">
                    <div class="flex gap-2 text-[12px]">
                      <button class="font-semibold text-brand-700 hover:underline" @click.stop="download(document)">Download</button>
                      <button class="font-semibold text-rose-600 hover:underline" @click.stop="remove(document)">Delete</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!documents.length">
                  <td colspan="5" class="dash-td py-8 text-center text-ink-400">No documents uploaded yet.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Extracted preview -->
      <div class="space-y-4">
        <div class="dash-card dash-card-pad">
          <div class="flex items-start gap-3">
            <span class="dash-icon-tile">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path d="M4 6h16M4 12h16M4 18h10" stroke-linecap="round" />
              </svg>
            </span>
            <div class="min-w-0">
              <p class="dash-section-title">Extracted text preview</p>
              <p class="dash-section-sub mt-0.5 truncate">{{ selected?.name ?? 'No file selected' }}</p>
            </div>
          </div>
          <div class="mt-3 max-h-[280px] overflow-y-auto rounded-xl bg-surface-50 p-3 font-mono text-[11px] leading-relaxed text-ink-600">
            <template v-if="selected?.extractions?.length">
              <p
                v-if="selected.processingError"
                class="mb-2 font-sans text-[11px] font-semibold"
                :class="selected.processingStatus === 'PROCESSED' ? 'text-brand-700' : 'text-amber-700'"
              >
                {{ selected.processingStatus === 'PROCESSED' ? 'Note:' : 'Reason:' }} {{ selected.processingError }}
              </p>
              <p v-for="item in selected.extractions" :key="item.id" class="mb-1.5">
                <span class="font-semibold text-ink-800">{{ item.label || item.fieldName }}:</span> {{ item.value }}
                <span v-if="item.evidence" class="block text-[10px] text-ink-400">“…{{ item.evidence }}…”</span>
              </p>
            </template>
            <p v-else-if="selected">
              {{ selected.name }}<br />
              Uploaded: {{ formatDateTime(selected.createdAt) }}<br />
              Pages: {{ selected.pageCount ?? '—' }}<br />
              Status: {{ statusText(selected.processingStatus) }}
              <template v-if="selected.processingError">
                <br />
                {{ selected.processingStatus === 'PROCESSED' ? 'Note:' : 'Reason:' }}
                {{ selected.processingError }}
              </template>
              <span
                v-if="selected.processingStatus === 'PROCESSED'"
                class="mt-2 block rounded-lg border border-sky-200 bg-sky-50 p-2 font-sans text-[11px] leading-snug text-sky-800"
              >
                Extraction succeeded, but no recognizable medical values (e.g. HbA1c, blood pressure, glucose,
                weight or height) were found in this document — so there is nothing to review or attach. The
                extracted text itself is stored and searchable.
              </span>
              <span
                v-else-if="selected.processingStatus === 'FAILED' && (selected.processingError || '').includes('No text layer')"
                class="mt-2 block rounded-lg border border-amber-200 bg-amber-50 p-2 font-sans text-[11px] leading-snug text-amber-800"
              >
                This document is a scan (images only) and OCR is unavailable on the server right now. Upload the
                original digital PDF or an export with selectable text instead.
              </span>
            </p>
            <p v-else>Select a file to preview its extracted text.</p>
          </div>
          <button class="dash-btn mt-4 w-full" :disabled="!pendingCount()" @click="attachAll">
            {{ pendingCount() ? `Attach ${pendingCount()} value${pendingCount() === 1 ? '' : 's'} to my records` : 'All values attached to my records' }}
          </button>
          <button
            v-if="selected && selected.processingStatus === 'PROCESSED'"
            class="btn-secondary mt-2 w-full text-xs"
            @click="askAi"
          >
            Ask the AI assistant about this document
          </button>
          <p
            v-if="selected && !selected?.extractions?.length && selected.processingStatus === 'PROCESSED'"
            class="mt-2 text-center text-[11px] text-ink-400"
          >
            Attaching becomes available once medical values are detected — try uploading a lab report with
            quantities like HbA1c, blood pressure or weight.
          </p>
          <p v-if="attachedMsg" class="mt-2 text-center text-[11px] font-semibold text-brand-700">{{ attachedMsg }}</p>
        </div>

        <div v-if="selected?.extractions?.length" class="dash-card dash-card-pad">
          <div class="flex items-center justify-between">
            <p class="text-sm font-bold text-ink-800">Review extractions</p>
            <span v-if="pendingCount()" class="chip bg-amber-50 text-amber-700">{{ pendingCount() }} pending</span>
            <span v-else class="chip bg-brand-50 text-brand-700">All reviewed</span>
          </div>
          <div class="mt-3 space-y-2">
            <div v-for="item in selected.extractions" :key="item.id" class="rounded-xl border border-ink-200 px-3 py-2">
              <div class="flex items-center justify-between gap-2">
                <p class="text-[12px] font-semibold text-ink-800">{{ item.label || item.fieldName }}</p>
                <span class="chip whitespace-nowrap" :class="reviewChip(item.reviewStatus)">{{ item.reviewStatus.toLowerCase() }}</span>
              </div>
              <p class="mt-1 text-[12px] text-ink-600">{{ item.value }}</p>
              <div class="mt-2 flex gap-1.5">
                <button class="btn-secondary px-2 py-1 text-[10px]" @click="review(item.id, 'CONFIRMED')">Confirm</button>
                <button class="btn-secondary px-2 py-1 text-[10px]" @click="review(item.id, 'CORRECTED', item.value)">Correct</button>
                <button class="btn-danger px-2 py-1 text-[10px]" @click="review(item.id, 'REJECTED')">Reject</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
