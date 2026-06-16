<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useImageStore } from '@/stores/imageStore'
import { useClassificationStore } from '@/stores/classificationStore'
import { useImageLoader } from '@/composables/useImageLoader'
import { useHeatmap } from '@/composables/useHeatmap'
import { ElMessage } from 'element-plus'
import type { ImageInfo, TileClassification, SubstrateClass, HeatmapTile } from '@/types'
import { SUBSTRATE_TYPES } from '@/types'

const CLASS_NAMES: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.name
  return acc
}, {} as Record<string, string>)

const CLASS_COLORS: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.color
  return acc
}, {} as Record<string, string>)

const props = defineProps<{
  zoomInTrigger?: number
  zoomOutTrigger?: number
  resetViewTrigger?: number
}>()

const emit = defineEmits<{
  (e: 'tile-selected', tile: TileClassification | null): void
}>()

const imageStore = useImageStore()
const classificationStore = useClassificationStore()
const { 
  initViewer, 
  viewer, 
  isReady, 
  zoom, 
  screenToImageCoordinates, 
  zoomTo, 
  resetView, 
  destroy: destroyViewer 
} = useImageLoader()
const { renderHeatmap, getTileAtPosition, highlightTile } = useHeatmap()

const viewerContainer = ref<HTMLElement | null>(null)
const heatmapCanvas = ref<HTMLCanvasElement | null>(null)
const overlayContainer = ref<HTMLElement | null>(null)
const isViewerReady = ref(false)
const isLoading = computed(() => imageStore.loading || classificationStore.loading)
const currentImage = computed(() => imageStore.currentImage)
const dziUrl = computed(() => imageStore.dziUrl)
const showHeatmap = computed(() => classificationStore.heatmapData !== null)
const heatmapData = computed(() => classificationStore.heatmapData)
const selectedTile = computed(() => classificationStore.selectedTile)

const hoveredTile = ref<any>(null)
const showTileInfo = ref(false)
const tileInfoPosition = ref({ x: 0, y: 0 })

const animationFrameId = ref<number | null>(null)

watch(
  () => currentImage.value,
  async (newImage) => {
    if (newImage && viewerContainer.value && dziUrl.value) {
      try {
        destroyViewer()
        isViewerReady.value = false
        await nextTick()
        await initViewer(newImage, viewerContainer.value, dziUrl.value)
        isViewerReady.value = true
        setupHeatmapOverlay(newImage)
      } catch (error: any) {
        ElMessage.error(error.message || '图像加载失败')
      }
    }
  }
)

watch(
  () => props.zoomInTrigger,
  () => {
    zoomTo(1.2)
  }
)

watch(
  () => props.zoomOutTrigger,
  () => {
    zoomTo(0.8)
  }
)

watch(
  () => props.resetViewTrigger,
  () => {
    resetView()
  }
)

watch(
  () => heatmapData.value,
  (newData) => {
    if (newData && viewer.value && currentImage.value) {
      nextTick(() => {
        updateHeatmap()
      })
    }
  }
)

watch(
  () => [zoom.value, isReady.value],
  () => {
    if (showHeatmap.value && viewer.value && currentImage.value) {
      updateHeatmap()
    }
  }
)

function setupHeatmapOverlay(imageData: ImageInfo) {
  if (!overlayContainer.value || !viewer.value) return

  overlayContainer.value.innerHTML = ''

  const container = document.createElement('div')
  container.style.position = 'absolute'
  container.style.top = '0'
  container.style.left = '0'
  container.style.width = '100%'
  container.style.height = '100%'
  container.style.pointerEvents = 'none'
  container.style.zIndex = '10'

  const canvas = document.createElement('canvas')
  canvas.style.position = 'absolute'
  canvas.style.top = '0'
  canvas.style.left = '0'
  canvas.style.pointerEvents = 'none'
  canvas.style.willChange = 'transform'
  container.appendChild(canvas)

  overlayContainer.value.appendChild(container)
  heatmapCanvas.value = canvas

  viewer.value.addHandler('update-viewport', updateHeatmap)
  viewer.value.addHandler('canvas-click', handleCanvasClick)
  viewer.value.addHandler('canvas-move', handleCanvasMove)
}

function getEffectiveClass(tile: HeatmapTile): SubstrateClass {
  return tile.actual_class
}

function updateHeatmap() {
  if (!heatmapCanvas.value || !viewer.value || !currentImage.value || !heatmapData.value) return

  const viewport = viewer.value.viewport
  const containerSize = viewer.value.container.getBoundingClientRect()
  const contentSize = viewport.getContentSize()

  const imageWidth = currentImage.value.width
  const imageHeight = currentImage.value.height

  const viewportTopLeft = viewport.getBounds(true)
  const scale = containerSize.width / viewportTopLeft.width / contentSize.x * imageWidth

  const offsetX = -viewportTopLeft.x * scale
  const offsetY = -viewportTopLeft.y * scale

  renderHeatmap(heatmapCanvas.value, viewer.value.container, scale, offsetX, offsetY)

  if (selectedTile.value && heatmapData.value) {
    const tileData = heatmapData.value.tile_data.find(t => t.tile_id === selectedTile.value?.tile_id)
    if (tileData) {
      highlightTile(tileData, heatmapCanvas.value, scale)
    }
  }
}

function handleCanvasClick(event: any) {
  if (!currentImage.value || !heatmapData.value) return

  const webPoint = event.position
  const imageCoords = screenToImageCoordinates(webPoint.x, webPoint.y, currentImage.value)

  if (imageCoords) {
    const tile = getTileAtPosition(imageCoords.x, imageCoords.y)
    if (tile) {
      const fullTileInfo = classificationStore.classificationResults?.results.find(t => t.tile_id === tile.tile_id)
      if (fullTileInfo) {
        classificationStore.selectTile(fullTileInfo)
        emit('tile-selected', fullTileInfo)
      }
    } else {
      classificationStore.selectTile(null)
      emit('tile-selected', null)
    }
  }
}

function handleCanvasMove(event: any) {
  if (!currentImage.value || !heatmapData.value) return

  const webPoint = event.position

  const imageCoords = screenToImageCoordinates(webPoint.x, webPoint.y, currentImage.value)
  if (imageCoords) {
    const tile = getTileAtPosition(imageCoords.x, imageCoords.y)
    hoveredTile.value = tile
    showTileInfo.value = !!tile
    tileInfoPosition.value = {
      x: webPoint.x + 15,
      y: webPoint.y + 15
    }
  }
}

function getDisplayClass(classType: string): string {
  return CLASS_NAMES[classType] || classType
}

function getDisplayColor(classType: string): string {
  return CLASS_COLORS[classType] || '#64748b'
}

function animate() {
  updateHeatmap()
  animationFrameId.value = requestAnimationFrame(animate)
}

onMounted(() => {
  if (currentImage.value && viewerContainer.value && dziUrl.value) {
    initViewer(currentImage.value, viewerContainer.value, dziUrl.value).then(() => {
      isViewerReady.value = true
      setupHeatmapOverlay(currentImage.value!)
      animate()
    })
  } else {
    animate()
  }
})

onUnmounted(() => {
  if (animationFrameId.value) {
    cancelAnimationFrame(animationFrameId.value)
  }
})
</script>

<template>
  <div class="image-viewer relative w-full h-full bg-slate-950 overflow-hidden">
    <div
      ref="viewerContainer"
      class="w-full h-full"
    ></div>

    <div
      ref="overlayContainer"
      class="absolute inset-0 pointer-events-none"
    ></div>

    <div
      v-if="!currentImage"
      class="absolute inset-0 flex items-center justify-center"
    >
      <div class="text-center">
        <div class="w-32 h-32 mx-auto mb-6 rounded-3xl bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center border border-slate-700">
          <svg class="w-16 h-16 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <h3 class="text-slate-300 text-xl font-medium mb-2">上传声呐图像开始分析</h3>
        <p class="text-slate-500 text-sm">支持 PNG、TIFF 格式，最大 20k×20k 像素</p>
      </div>
    </div>

    <div
      v-if="isLoading && !classificationStore.isProcessing"
      class="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50"
    >
      <div class="text-center">
        <div class="w-16 h-16 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-white text-lg font-medium">加载中...</p>
      </div>
    </div>

    <div
      v-if="showTileInfo && hoveredTile"
      class="absolute z-50 pointer-events-none"
      :style="{ left: `${tileInfoPosition.x}px`, top: `${tileInfoPosition.y}px` }"
    >
      <div class="bg-slate-900/95 backdrop-blur-md rounded-lg p-3 border border-slate-700 shadow-lg min-w-[180px]">
        <div class="flex items-center gap-2 mb-2">
          <div
            class="w-4 h-4 rounded"
            :style="{ backgroundColor: getDisplayColor(getEffectiveClass(hoveredTile)) }"
          ></div>
          <span class="text-white font-medium">{{ getDisplayClass(getEffectiveClass(hoveredTile)) }}</span>
        </div>
        <div class="text-slate-400 text-sm space-y-1">
          <div class="flex justify-between">
            <span>置信度</span>
            <span class="text-cyan-400 font-mono">{{ (hoveredTile.confidence * 100).toFixed(1) }}%</span>
          </div>
          <div class="flex justify-between">
            <span>图块位置</span>
            <span class="font-mono">({{ hoveredTile.tile_x }}, {{ hoveredTile.tile_y }})</span>
          </div>
          <div v-if="hoveredTile.is_corrected" class="text-amber-400 text-xs mt-1">
            已人工修正
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="currentImage && isReady"
      class="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur-md rounded-lg px-4 py-2 border border-slate-700 z-30"
    >
      <div class="flex items-center gap-4 text-sm">
        <div class="text-slate-300">
          <span class="text-slate-500">尺寸:</span>
          <span class="text-white font-mono ml-1">{{ currentImage.width }} × {{ currentImage.height }}</span>
        </div>
        <div class="text-slate-300">
          <span class="text-slate-500">缩放:</span>
          <span class="text-white font-mono ml-1">{{ (zoom * 100).toFixed(0) }}%</span>
        </div>
        <div class="text-slate-300">
          <span class="text-slate-500">图块:</span>
          <span class="text-white font-mono ml-1">{{ currentImage.num_tiles_x }} × {{ currentImage.num_tiles_y }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.image-viewer {
  min-height: 400px;
}

.image-viewer :deep(.openseadragon-container) {
  background: rgb(2, 6, 23) !important;
}

.image-viewer :deep(.openseadragon-canvas) {
  outline: none !important;
}

.image-viewer :deep(.navigator) {
  background: rgba(15, 23, 42, 0.9) !important;
  border: 1px solid rgba(6, 182, 212, 0.3) !important;
  border-radius: 8px !important;
  overflow: hidden !important;
}

.image-viewer :deep(.navigator-displayregion) {
  background: rgba(6, 182, 212, 0.2) !important;
  border: 2px solid #06b6d4 !important;
}
</style>
