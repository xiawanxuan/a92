<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useImageStore } from '@/stores/imageStore'
import { useClassificationStore } from '@/stores/classificationStore'
import { useImageLoader } from '@/composables/useImageLoader'
import { useHeatmap } from '@/composables/useHeatmap'
import { ElMessage } from 'element-plus'
import type { ImageInfo, TileClassification, SubstrateClass, HeatmapTile, GradCAMResult } from '@/types'
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
const gradCamCanvas = ref<HTMLCanvasElement | null>(null)
const overlayContainer = ref<HTMLElement | null>(null)
const isViewerReady = ref(false)
const isLoading = computed(() => imageStore.loading || classificationStore.loading)
const currentImage = computed(() => imageStore.currentImage)
const dziUrl = computed(() => imageStore.dziUrl)
const showHeatmap = computed(() => classificationStore.heatmapData !== null)
const heatmapData = computed(() => classificationStore.heatmapData)
const selectedTile = computed(() => classificationStore.selectedTile)

const gradCamEnabled = computed(() => classificationStore.gradCamOverlaySettings.enabled)
const gradCamOpacity = computed(() => classificationStore.gradCamOverlaySettings.opacity)
const gradCamShowBbox = computed(() => classificationStore.gradCamOverlaySettings.show_bbox)
const gradCamColormap = computed(() => classificationStore.gradCamOverlaySettings.heatmap_colormap)
const gradCamResults = computed(() => classificationStore.gradCamResults)
const gradCamHeatmaps = computed(() => classificationStore.gradCamHeatmaps)
const selectedGradCam = computed(() => classificationStore.selectedGradCam)

const loadedHeatmapData = new Map<string, ImageData>()
const loadingHeatmapIds = new Set<string>()

const hoveredTile = ref<any>(null)
const hoveredGradCam = ref<GradCAMResult | null>(null)
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

watch(
  () => [gradCamEnabled.value, gradCamOpacity.value, gradCamShowBbox.value, gradCamColormap.value, gradCamResults.value.length],
  () => {
    if (gradCamEnabled.value && viewer.value && currentImage.value) {
      updateGradCamOverlay()
    } else if (gradCamCanvas.value) {
      const ctx = gradCamCanvas.value.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, gradCamCanvas.value.width, gradCamCanvas.value.height)
      }
    }
  }
)

function setupHeatmapOverlay(imageData: ImageInfo) {
  if (!overlayContainer.value || !viewer.value) return

  overlayContainer.value.innerHTML = ''

  const heatmapContainer = document.createElement('div')
  heatmapContainer.style.position = 'absolute'
  heatmapContainer.style.top = '0'
  heatmapContainer.style.left = '0'
  heatmapContainer.style.width = '100%'
  heatmapContainer.style.height = '100%'
  heatmapContainer.style.pointerEvents = 'none'
  heatmapContainer.style.zIndex = '10'

  const heatmapCanvasEl = document.createElement('canvas')
  heatmapCanvasEl.style.position = 'absolute'
  heatmapCanvasEl.style.top = '0'
  heatmapCanvasEl.style.left = '0'
  heatmapCanvasEl.style.pointerEvents = 'none'
  heatmapCanvasEl.style.willChange = 'transform'
  heatmapContainer.appendChild(heatmapCanvasEl)
  overlayContainer.value.appendChild(heatmapContainer)
  heatmapCanvas.value = heatmapCanvasEl

  const gradCamContainer = document.createElement('div')
  gradCamContainer.style.position = 'absolute'
  gradCamContainer.style.top = '0'
  gradCamContainer.style.left = '0'
  gradCamContainer.style.width = '100%'
  gradCamContainer.style.height = '100%'
  gradCamContainer.style.pointerEvents = 'none'
  gradCamContainer.style.zIndex = '15'

  const gradCamCanvasEl = document.createElement('canvas')
  gradCamCanvasEl.style.position = 'absolute'
  gradCamCanvasEl.style.top = '0'
  gradCamCanvasEl.style.left = '0'
  gradCamCanvasEl.style.pointerEvents = 'none'
  gradCamCanvasEl.style.willChange = 'transform'
  gradCamContainer.appendChild(gradCamCanvasEl)
  overlayContainer.value.appendChild(gradCamContainer)
  gradCamCanvas.value = gradCamCanvasEl

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

  if (gradCamEnabled.value) {
    updateGradCamOverlay()
  }
}

function applyColormap(value: number, colormap: string): [number, number, number] {
  const v = Math.max(0, Math.min(1, value))

  if (colormap === 'jet') {
    let r = 0, g = 0, b = 0
    if (v < 0.125) {
      r = 0; g = 0; b = 0.5 + v * 4
    } else if (v < 0.375) {
      r = 0; g = (v - 0.125) * 4; b = 1
    } else if (v < 0.625) {
      r = (v - 0.375) * 4; g = 1; b = 1 - (v - 0.375) * 4
    } else if (v < 0.875) {
      r = 1; g = 1 - (v - 0.625) * 4; b = 0
    } else {
      r = 1 - (v - 0.875) * 4; g = 0; b = 0
    }
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)]
  } else if (colormap === 'hot') {
    const r = Math.min(1, v * 1.5)
    const g = Math.max(0, Math.min(1, (v - 0.33) * 1.5))
    const b = Math.max(0, Math.min(1, (v - 0.67) * 3))
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)]
  } else if (colormap === 'viridis') {
    const stops = [
      [0.267, 0.004, 0.329],
      [0.283, 0.141, 0.458],
      [0.254, 0.265, 0.530],
      [0.207, 0.372, 0.553],
      [0.164, 0.471, 0.558],
      [0.128, 0.567, 0.551],
      [0.135, 0.659, 0.518],
      [0.267, 0.749, 0.441],
      [0.478, 0.821, 0.318],
      [0.741, 0.873, 0.150],
      [0.993, 0.906, 0.144]
    ]
    const idx = v * (stops.length - 1)
    const i = Math.floor(idx)
    const t = idx - i
    if (i >= stops.length - 1) {
      const s = stops[stops.length - 1]
      return [Math.round(s[0] * 255), Math.round(s[1] * 255), Math.round(s[2] * 255)]
    }
    const s1 = stops[i]
    const s2 = stops[i + 1]
    return [
      Math.round((s1[0] + t * (s2[0] - s1[0])) * 255),
      Math.round((s1[1] + t * (s2[1] - s1[1])) * 255),
      Math.round((s1[2] + t * (s2[2] - s1[2])) * 255)
    ]
  } else if (colormap === 'plasma') {
    const stops = [
      [0.052, 0.029, 0.529],
      [0.279, 0.011, 0.624],
      [0.480, 0.028, 0.642],
      [0.655, 0.133, 0.590],
      [0.797, 0.277, 0.484],
      [0.906, 0.443, 0.353],
      [0.980, 0.625, 0.208],
      [0.995, 0.816, 0.068],
      [0.940, 0.975, 0.131]
    ]
    const idx = v * (stops.length - 1)
    const i = Math.floor(idx)
    const t = idx - i
    if (i >= stops.length - 1) {
      const s = stops[stops.length - 1]
      return [Math.round(s[0] * 255), Math.round(s[1] * 255), Math.round(s[2] * 255)]
    }
    const s1 = stops[i]
    const s2 = stops[i + 1]
    return [
      Math.round((s1[0] + t * (s2[0] - s1[0])) * 255),
      Math.round((s1[1] + t * (s2[1] - s1[1])) * 255),
      Math.round((s1[2] + t * (s2[2] - s1[2])) * 255)
    ]
  }
  return [255, 0, 0]
}

function heatmapArrayToImageData(heatmapArray: number[][], colormap: string, opacity: number): ImageData {
  const height = heatmapArray.length
  const width = heatmapArray[0].length
  const data = new Uint8ClampedArray(width * height * 4)

  let maxVal = 0
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      maxVal = Math.max(maxVal, heatmapArray[y][x])
    }
  }

  const scale = maxVal > 0 ? 1 / maxVal : 1

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const val = heatmapArray[y][x] * scale
      const [r, g, b] = applyColormap(val, colormap)
      const idx = (y * width + x) * 4
      data[idx] = r
      data[idx + 1] = g
      data[idx + 2] = b
      data[idx + 3] = Math.round(val * opacity * 255)
    }
  }

  return new ImageData(data, width, height)
}

async function ensureHeatmapImageData(gradCam: GradCAMResult): Promise<ImageData | null> {
  const cacheKey = `${gradCam.id}_${gradCamColormap.value}_${gradCamOpacity.value}`
  const cached = loadedHeatmapData.get(cacheKey)
  if (cached) return cached

  if (loadingHeatmapIds.has(gradCam.id)) return null
  loadingHeatmapIds.add(gradCam.id)

  try {
    const heatmapData = await classificationStore.loadGradCamHeatmap(gradCam.id)
    if (heatmapData && heatmapData.heatmap) {
      const imageData = heatmapArrayToImageData(
        heatmapData.heatmap,
        gradCamColormap.value,
        gradCamOpacity.value
      )
      loadedHeatmapData.set(cacheKey, imageData)
      return imageData
    }
  } finally {
    loadingHeatmapIds.delete(gradCam.id)
  }
  return null
}

async function updateGradCamOverlay() {
  if (!gradCamCanvas.value || !viewer.value || !currentImage.value) return

  const containerSize = viewer.value.container.getBoundingClientRect()
  gradCamCanvas.value.width = containerSize.width
  gradCamCanvas.value.height = containerSize.height

  const ctx = gradCamCanvas.value.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, gradCamCanvas.value.width, gradCamCanvas.value.height)

  if (!gradCamEnabled.value || gradCamResults.value.length === 0) return

  const viewport = viewer.value.viewport
  const contentSize = viewport.getContentSize()
  const imageWidth = currentImage.value.width
  const imageHeight = currentImage.value.height

  const viewportTopLeft = viewport.getBounds(true)
  const scale = containerSize.width / viewportTopLeft.width / contentSize.x * imageWidth
  const offsetX = -viewportTopLeft.x * scale
  const offsetY = -viewportTopLeft.y * scale

  const tileSize = heatmapData.value?.tile_size || 512

  for (const gradCam of gradCamResults.value) {
    const tilePixelX = gradCam.tile_x * tileSize
    const tilePixelY = gradCam.tile_y * tileSize

    const screenX = tilePixelX * scale / imageWidth * containerSize.width + offsetX
    const screenY = tilePixelY * scale / imageHeight * containerSize.height + offsetY
    const screenW = tileSize * scale / imageWidth * containerSize.width
    const screenH = tileSize * scale / imageHeight * containerSize.height

    if (screenX + screenW < 0 || screenX > containerSize.width ||
        screenY + screenH < 0 || screenY > containerSize.height) {
      continue
    }

    const imageData = await ensureHeatmapImageData(gradCam)
    if (imageData) {
      const tmpCanvas = document.createElement('canvas')
      tmpCanvas.width = imageData.width
      tmpCanvas.height = imageData.height
      const tmpCtx = tmpCanvas.getContext('2d')
      if (tmpCtx) {
        tmpCtx.putImageData(imageData, 0, 0)
        ctx.globalAlpha = gradCamOpacity.value
        ctx.drawImage(tmpCanvas, screenX, screenY, screenW, screenH)
        ctx.globalAlpha = 1
      }
    }

    if (gradCamShowBbox.value && gradCam.bbox) {
      const bboxScreenX = screenX + gradCam.bbox.x / tileSize * screenW
      const bboxScreenY = screenY + gradCam.bbox.y / tileSize * screenH
      const bboxScreenW = gradCam.bbox.width / tileSize * screenW
      const bboxScreenH = gradCam.bbox.height / tileSize * screenH

      ctx.strokeStyle = '#ef4444'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 3])
      ctx.strokeRect(bboxScreenX, bboxScreenY, bboxScreenW, bboxScreenH)
      ctx.setLineDash([])

      ctx.fillStyle = 'rgba(239, 68, 68, 0.9)'
      ctx.fillRect(bboxScreenX, bboxScreenY - 20, 80, 20)
      ctx.fillStyle = '#fff'
      ctx.font = '11px monospace'
      ctx.fillText(`${(gradCam.confidence * 100).toFixed(0)}%`, bboxScreenX + 4, bboxScreenY - 6)
    }

    if (selectedGradCam.value?.id === gradCam.id) {
      ctx.strokeStyle = '#fbbf24'
      ctx.lineWidth = 3
      ctx.strokeRect(screenX, screenY, screenW, screenH)
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

      const gradCamResult = gradCamResults.value.find(
        g => g.tile_x === tile.tile_x && g.tile_y === tile.tile_y
      )
      classificationStore.selectGradCam(gradCamResult || null)
    } else {
      classificationStore.selectTile(null)
      classificationStore.selectGradCam(null)
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

    if (tile && gradCamEnabled.value) {
      hoveredGradCam.value = gradCamResults.value.find(
        g => g.tile_x === tile.tile_x && g.tile_y === tile.tile_y
      ) || null
    } else {
      hoveredGradCam.value = null
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
      <div class="bg-slate-900/95 backdrop-blur-md rounded-lg p-3 border border-slate-700 shadow-lg min-w-[200px]">
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

          <div v-if="hoveredGradCam" class="mt-3 pt-3 border-t border-slate-700">
            <div class="flex items-center gap-1 text-red-400 text-xs font-medium mb-2">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              Grad-CAM 目标定位
            </div>
            <div class="space-y-1 text-xs">
              <div class="flex justify-between">
                <span class="text-slate-500">置信度</span>
                <span class="text-red-400 font-mono">{{ (hoveredGradCam.confidence * 100).toFixed(1) }}%</span>
              </div>
              <div v-if="hoveredGradCam.bbox" class="flex justify-between">
                <span class="text-slate-500">尺寸</span>
                <span class="font-mono">{{ hoveredGradCam.bbox.width.toFixed(0) }} × {{ hoveredGradCam.bbox.height.toFixed(0) }}</span>
              </div>
              <div v-if="hoveredGradCam.bbox" class="flex justify-between">
                <span class="text-slate-500">面积占比</span>
                <span class="font-mono">{{ (hoveredGradCam.bbox.area_ratio * 100).toFixed(1) }}%</span>
              </div>
            </div>
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

input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
  transition: transform 0.2s;
}

input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

input[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
}
</style>
