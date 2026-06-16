<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ToolBar from '@/components/ToolBar.vue'
import ImageViewer from '@/components/ImageViewer.vue'
import ControlPanel from '@/components/ControlPanel.vue'
import StatsCharts from '@/components/StatsCharts.vue'
import { useImageStore } from '@/stores/imageStore'
import { useClassificationStore } from '@/stores/classificationStore'

const route = useRoute()
const router = useRouter()
const imageStore = useImageStore()
const classificationStore = useClassificationStore()

const handleImageIdFromUrl = () => {
  const imageId = route.query.image_id as string
  if (imageId && !imageStore.currentImage) {
    imageStore.loadImage(imageId)
  }
}

const handleRouterQueryChange = () => {
  if (route.path === '/') {
    handleImageIdFromUrl()
  }
}

watch(() => route.query, handleRouterQueryChange, { deep: true })

onMounted(() => {
  handleImageIdFromUrl()
  
  imageStore.loadImageList().catch(err => {
    console.warn('加载图像列表失败:', err)
  })
})

onBeforeUnmount(() => {
  classificationStore.stopPolling()
})
</script>

<template>
  <div class="home-page flex flex-col h-screen overflow-hidden bg-slate-900">
    <header class="flex-shrink-0 z-10">
      <ToolBar />
    </header>
    
    <main class="flex-1 flex overflow-hidden">
      <section class="flex-1 flex flex-col overflow-hidden">
        <div class="flex-1 relative overflow-hidden">
          <ImageViewer />
        </div>
        
        <div class="flex-shrink-0 h-[320px] p-3 border-t border-slate-700 bg-slate-900">
          <StatsCharts />
        </div>
      </section>
      
      <aside class="flex-shrink-0 w-[340px] border-l border-slate-700 overflow-hidden">
        <ControlPanel />
      </aside>
    </main>
    
    <div 
      v-if="classificationStore.isProcessing" 
      class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
    >
      <div class="bg-slate-800 px-6 py-4 rounded-xl shadow-2xl border border-slate-600 min-w-[360px]">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center">
            <svg class="w-5 h-5 text-cyan-400 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <div class="flex-1">
            <div class="text-white font-medium">AI 正在分析声呐图像</div>
            <div class="text-slate-400 text-sm">
              {{ classificationStore.currentTask?.processed_tiles || 0 }} / {{ classificationStore.currentTask?.total_tiles || 0 }} 图块
            </div>
          </div>
        </div>
        
        <div class="relative h-2 bg-slate-700 rounded-full overflow-hidden">
          <div 
            class="absolute top-0 left-0 h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-300"
            :style="{ width: `${classificationStore.progressPercent}%` }"
          ></div>
        </div>
        
        <div class="flex justify-between mt-2 text-xs">
          <span class="text-slate-400">{{ classificationStore.progressPercent }}%</span>
          <span class="text-cyan-400">{{ classificationStore.progressStatus }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
}
</style>
