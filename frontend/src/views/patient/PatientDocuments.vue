<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { patient } from '@/api/endpoints';
import { formatBytes, formatDateTime } from '@/composables/useAsync';
import type { DocumentRecord } from '@/api/types';

const { t } = useI18n();

const documents = ref<DocumentRecord[]>([]);
const selected = ref<DocumentRecord | null>(null);
const loading = ref(false);
const uploading = ref(false);
const dragging = ref(false);
const error = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const category = ref('OTHER');

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
  for (const item of selected.value.extractions) {
    if (item.reviewStatus === 'PENDING' || item.reviewStatus === 'NEEDS_REVIEW') {
      await patient.reviewExtraction(selected.value.id, item.id, 'CONFIRMED');
    }
  }
  selected.value = await patient.document(selected.value.id);
  await load();
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
      <select v-model="category" class="input w-44 text-xs" aria-label="Document category">
        <option value="OTHER">Other</option>
        <option value="LAB">Lab report</option>
        <option value="IMAGING">Imaging</option>
        <option value="PRESCRIPTION">Prescription</option>
        <option value="LETTER">Letter</option>
      </select>
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
              <p class="dash-section-title">Uploaded files</p>
              <p class="dash-section-sub mt-0.5">Extraction status and source documents</p>
            </div>
          </div>
          <div v-if="loading" class="h-28 animate-pulse bg-ink-100" />
          <div v-else class="overflow-x-auto">
            <table class="w-full min-w-[560px] border-collapse">
              <thead class="bg-surface-50">
                <tr>
                  <th class="dash-th">Filename</th>
                  <th class="dash-th">Size</th>
                  <th class="dash-th">Status</th>
                  <th class="dash-th">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="document in documents" :key="document.id" class="dash-row">
                  <td class="dash-td">
                    <button class="font-medium text-brand-700 hover:underline" @click="open(document)">{{ document.name }}</button>
                  </td>
                  <td class="dash-td">{{ formatBytes(document.sizeBytes) }}</td>
                  <td class="dash-td">
                    <span class="chip" :class="document.processingStatus === 'PROCESSED' ? 'bg-brand-50 text-brand-700' : 'bg-amber-50 text-amber-700'">
                      {{ statusText(document.processingStatus) }}
                    </span>
                  </td>
                  <td class="dash-td">
                    <div class="flex gap-2 text-[12px]">
                      <button class="font-semibold text-brand-700 hover:underline" @click="download(document)">Download</button>
                      <button class="font-semibold text-rose-600 hover:underline" @click="remove(document)">Cancel</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!documents.length">
                  <td colspan="4" class="dash-td py-8 text-center text-ink-400">No documents uploaded yet.</td>
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
            </p>
            <p v-else>Select a file to preview its extracted text.</p>
          </div>
          <button class="dash-btn mt-4 w-full" :disabled="!selected?.extractions?.length" @click="attachAll">
            Attach document to your digital twin records
          </button>
        </div>

        <div v-if="selected?.extractions?.length" class="dash-card dash-card-pad">
          <p class="text-sm font-bold text-ink-800">Review extractions</p>
          <div class="mt-3 space-y-2">
            <div v-for="item in selected.extractions" :key="item.id" class="rounded-xl border border-ink-200 px-3 py-2">
              <div class="flex items-center justify-between gap-2">
                <p class="text-[12px] font-semibold text-ink-800">{{ item.label || item.fieldName }}</p>
                <span class="chip bg-surface-100 text-ink-600">{{ item.reviewStatus }}</span>
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
