<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useImageStore } from '@/stores/imageStore'
import { useClassificationStore } from '@/stores/classificationStore'
import { exportReport } from '@/api/classification'

const router = useRouter()
const imageStore = useImageStore()
const classificationStore = useClassificationStore()

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

const hasImage = computed(() => imageStore.hasImage)
const isProcessing = computed(() => classificationStore.isProcessing)
const isCompleted = computed(() => classificationStore.isCompleted)
const currentImage = computed(() => imageStore.currentImage)
const currentTask = computed(() => classificationStore.currentTask)

const emit = defineEmits<{
  (e: 'zoom-in'): void
  (e: 'zoom-out'): void
  (e: 'reset-view'): void
}>()

function handleFileClick() {
  fileInputRef.value?.click()
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return

  const file = files[0]
  await processFile(file)
  target.value = ''
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

async function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragging.value = false

  const files = event.dataTransfer?.files
  if (!files || files.length === 0) return

  const file = files[0]
  await processFile(file)
}

async function processFile(file: File) {
  try {
    classificationStore.clearAll()
    await imageStore.upload(file)
  } catch (error: any) {
    ElMessage.error(error.message || '上传失败')
  }
}

async function startClassification() {
  if (!currentImage.value) return

  try {
    await classificationStore.start(currentImage.value.id)
    ElMessage.info('分类任务已启动，请等待完成...')
  } catch (error: any) {
    ElMessage.error(error.message || '启动分类失败')
  }
}

async function handleDownloadOriginal() {
  if (!currentImage.value) return

  try {
    await imageStore.download(currentImage.value.id)
  } catch (error: any) {
    ElMessage.error(error.message || '下载失败')
  }
}

async function handleExportReport() {
  if (!currentTask.value) return

  try {
    const blob = await exportReport(currentTask.value.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `classification_report_${currentTask.value.id}.json`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('报告导出成功')
  } catch (error: any) {
    ElMessage.error(error.message || '导出失败')
  }
}

function goToHistory() {
  router.push('/history')
}

function goToCorrections() {
  router.push('/corrections')
}

function handleRefresh() {
  if (currentTask.value) {
    classificationStore.loadAllData(currentTask.value.id)
  }
}
</script>

<template>
  <div
    class="toolbar h-16 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-slate-700 px-6 flex items-center justify-between"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div>
          <h1 class="text-white font-mono text-lg font-bold tracking-wider">SONAR CLASSIFIER</h1>
          <p class="text-slate-400 text-xs">海底底质智能分类系统</p>
        </div>
      </div>

      <div class="h-8 w-px bg-slate-700 mx-2"></div>

      <div class="flex items-center gap-2">
        <input
          ref="fileInputRef"
          type="file"
          class="hidden"
          accept=".png,.tif,.tiff"
          @change="handleFileChange"
        />

        <button
          class="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium hover:shadow-lg hover:shadow-cyan-500/30 transition-all duration-300"
          :class="{ 'opacity-50 cursor-not-allowed': isProcessing }"
          :disabled="isProcessing"
          @click="handleFileClick"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          <span>上传图像</span>
        </button>

        <button
          v-if="hasImage && !isCompleted"
          class="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-green-600 text-white font-medium hover:shadow-lg hover:shadow-emerald-500/30 transition-all duration-300"
          :class="{ 'opacity-50 cursor-not-allowed': isProcessing }"
          :disabled="isProcessing"
          @click="startClassification"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>开始分类</span>
        </button>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <template v-if="hasImage">
        <div class="flex items-center gap-1 bg-slate-800/50 rounded-lg p-1">
          <button
            class="p-2 rounded-md text-slate-300 hover:text-white hover:bg-slate-700/50 transition-all"
            title="放大"
            @click="$emit('zoom-in')"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </button>
          <button
            class="p-2 rounded-md text-slate-300 hover:text-white hover:bg-slate-700/50 transition-all"
            title="缩小"
            @click="$emit('zoom-out')"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
          </button>
          <button
            class="p-2 rounded-md text-slate-300 hover:text-white hover:bg-slate-700/50 transition-all"
            title="重置视图"
            @click="$emit('reset-view')"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>

        <div class="h-8 w-px bg-slate-700 mx-2"></div>
      </template>

      <button
        v-if="hasImage"
        class="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-700/50 transition-all"
        title="下载原始图像"
        @click="handleDownloadOriginal"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      </button>

      <button
        v-if="isCompleted"
        class="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-700/50 transition-all"
        title="导出报告"
        @click="handleExportReport"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </button>

      <button
        v-if="isCompleted"
        class="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-700/50 transition-all"
        title="刷新数据"
        @click="handleRefresh"
      >
        <svg class="w-4 h-4" :class="{ 'animate-spin': classificationStore.loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>

      <div class="h-8 w-px bg-slate-700 mx-2"></div>

      <button
        class="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-700/50 transition-all"
        title="历史记录"
        @click="goToHistory"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="hidden sm:inline">历史</span>
      </button>

      <button
        class="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-300 hover:bg-slate-700/50 transition-all"
        title="修正记录"
        @click="goToCorrections"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        <span class="hidden sm:inline">修正</span>
      </button>
    </div>

    <div
      v-if="isDragging"
      class="fixed inset-0 bg-slate-900/90 backdrop-blur-sm z-50 flex items-center justify-center"
    >
      <div class="text-center">
        <svg class="w-16 h-16 text-cyan-500 mx-auto mb-4 animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="text-white text-xl font-medium">释放以上传声呐图像</p>
        <p class="text-slate-400 mt-2">支持 PNG、TIFF 格式</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  position: relative;
  z-index: 100;
}
</style>
