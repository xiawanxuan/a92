import { ref, computed, watch } from 'vue'
import type { HeatmapDataResponse, HeatmapTile, SubstrateClass } from '@/types'
import { SUBSTRATE_TYPES } from '@/types'
import { useClassificationStore } from '@/stores/classificationStore'

const CLASS_COLORS: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.color
  return acc
}, {} as Record<string, string>)

export function useHeatmap() {
  const classificationStore = useClassificationStore()
  const canvas = ref<HTMLCanvasElement | null>(null)
  const container = ref<HTMLElement | null>(null)
  const isRendering = ref(false)

  const heatmapData = computed(() => classificationStore.heatmapData)
  const opacity = computed(() => classificationStore.heatmapSettings.opacity)
  const hiddenClasses = computed(() => new Set(classificationStore.heatmapSettings.hidden_classes))
  const showGrid = computed(() => classificationStore.heatmapSettings.show_grid)

  function hexToRgb(hex: string): { r: number; g: number; b: number } {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16)
        }
      : { r: 0, g: 0, b: 0 }
  }

  function getEffectiveClass(tile: HeatmapTile): SubstrateClass {
    return tile.actual_class
  }

  function renderHeatmap(
    canvasEl: HTMLCanvasElement,
    containerEl: HTMLElement,
    scale: number,
    offsetX: number,
    offsetY: number
  ) {
    if (!heatmapData.value) return

    canvas.value = canvasEl
    container.value = containerEl
    isRendering.value = true

    const ctx = canvasEl.getContext('2d')
    if (!ctx) return

    const { tile_size, num_tiles_x, num_tiles_y, tile_data } = heatmapData.value
    const imageWidth = num_tiles_x * tile_size
    const imageHeight = num_tiles_y * tile_size

    canvasEl.width = imageWidth * scale
    canvasEl.height = imageHeight * scale
    canvasEl.style.width = `${imageWidth * scale}px`
    canvasEl.style.height = `${imageHeight * scale}px`
    canvasEl.style.transform = `translate(${offsetX}px, ${offsetY}px)`

    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height)

    const visibleTiles = tile_data.filter(tile =>
      !hiddenClasses.value.has(getEffectiveClass(tile))
    )

    for (const tile of visibleTiles) {
      const effectiveClass = getEffectiveClass(tile)
      const color = CLASS_COLORS[effectiveClass] || '#64748b'
      const rgb = hexToRgb(color)
      const alpha = opacity.value

      ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`
      ctx.fillRect(
        tile.pixel_x * scale,
        tile.pixel_y * scale,
        tile_size * scale,
        tile_size * scale
      )

      if (tile.is_corrected) {
        ctx.strokeStyle = '#FFFFFF'
        ctx.lineWidth = 2 * scale
        ctx.strokeRect(
          tile.pixel_x * scale,
          tile.pixel_y * scale,
          tile_size * scale,
          tile_size * scale
        )
      }
    }

    if (showGrid.value && scale > 0.5) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)'
      ctx.lineWidth = 1 * scale

      for (let x = 0; x <= num_tiles_x; x++) {
        ctx.beginPath()
        ctx.moveTo(x * tile_size * scale, 0)
        ctx.lineTo(x * tile_size * scale, imageHeight * scale)
        ctx.stroke()
      }

      for (let y = 0; y <= num_tiles_y; y++) {
        ctx.beginPath()
        ctx.moveTo(0, y * tile_size * scale)
        ctx.lineTo(imageWidth * scale, y * tile_size * scale)
        ctx.stroke()
      }
    }

    isRendering.value = false
  }

  function highlightTile(
    tile: HeatmapTile,
    canvasEl: HTMLCanvasElement,
    scale: number
  ) {
    const ctx = canvasEl.getContext('2d')
    if (!ctx || !heatmapData.value) return

    const { tile_size } = heatmapData.value
    const effectiveClass = getEffectiveClass(tile)
    const color = CLASS_COLORS[effectiveClass] || '#64748b'
    const rgb = hexToRgb(color)

    ctx.strokeStyle = '#FFFFFF'
    ctx.lineWidth = 4 * scale
    ctx.strokeRect(
      tile.pixel_x * scale,
      tile.pixel_y * scale,
      tile_size * scale,
      tile_size * scale
    )

    ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${opacity.value * 0.5})`
    ctx.fillRect(
      tile.pixel_x * scale,
      tile.pixel_y * scale,
      tile_size * scale,
      tile_size * scale
    )
  }

  function getTileAtPosition(
    imageX: number,
    imageY: number
  ): HeatmapTile | null {
    if (!heatmapData.value) return null

    const { tile_size, num_tiles_x, num_tiles_y, tile_data } = heatmapData.value
    const tileX = Math.floor(imageX / tile_size)
    const tileY = Math.floor(imageY / tile_size)

    if (tileX < 0 || tileX >= num_tiles_x || tileY < 0 || tileY >= num_tiles_y) {
      return null
    }

    return tile_data.find(t => t.tile_x === tileX && t.tile_y === tileY) || null
  }

  watch(
    () => [
      classificationStore.heatmapSettings.opacity,
      classificationStore.heatmapSettings.hidden_classes,
      classificationStore.heatmapSettings.show_grid
    ],
    () => {
      if (canvas.value && container.value && heatmapData.value) {
        const scale = parseFloat(canvas.value.style.width) / (heatmapData.value.num_tiles_x * heatmapData.value.tile_size)
        const match = canvas.value.style.transform.match(/translate\(([^,]+)px,\s*([^)]+)px\)/)
        const offsetX = match ? parseFloat(match[1]) : 0
        const offsetY = match ? parseFloat(match[2]) : 0
        renderHeatmap(canvas.value, container.value, scale, offsetX, offsetY)
      }
    },
    { deep: true }
  )

  return {
    canvas,
    container,
    isRendering,
    renderHeatmap,
    highlightTile,
    getTileAtPosition
  }
}
