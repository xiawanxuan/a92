import { ref, computed } from 'vue'
import { useClassificationStore } from '@/stores/classificationStore'
import { gradCamApi } from '@/api/gradCam'
import type { GradCAMResult, GradCAMHeatmapResponse } from '@/types'

export function useGradCAM() {
  const store = useClassificationStore()

  const results = computed(() => store.gradCamResults)
  const heatmaps = computed(() => store.gradCamHeatmaps)
  const selected = computed(() => store.selectedGradCam)
  const loading = computed(() => store.gradCamLoading)
  const overlaySettings = computed(() => store.gradCamOverlaySettings)
  const hasResults = computed(() => store.hasGradCamResults)

  async function loadResults(taskId: string, page = 1, pageSize = 200) {
    return store.loadGradCamResults(taskId, page, pageSize)
  }

  async function loadHeatmap(gradCamId: string): Promise<GradCAMHeatmapResponse | null> {
    return store.loadGradCamHeatmap(gradCamId)
  }

  async function getHeatmapImage(gradCamId: string, colormap = 'jet'): Promise<string | null> {
    return store.getGradCamHeatmapImage(gradCamId, colormap)
  }

  async function getByTile(taskId: string, tileX: number, tileY: number): Promise<GradCAMResult | null> {
    try {
      return await gradCamApi.getByTile(taskId, tileX, tileY)
    } catch (e) {
      return null
    }
  }

  function select(gradCam: GradCAMResult | null) {
    store.selectGradCam(gradCam)
  }

  function setEnabled(value: boolean) {
    store.setGradCamOverlayEnabled(value)
  }

  function setOpacity(value: number) {
    store.setGradCamOpacity(value)
  }

  function setShowBbox(value: boolean) {
    store.setGradCamShowBbox(value)
  }

  function setColormap(value: 'jet' | 'hot' | 'viridis' | 'plasma') {
    store.setGradCamColormap(value)
  }

  function clear() {
    store.selectGradCam(null)
  }

  return {
    results,
    heatmaps,
    selected,
    loading,
    overlaySettings,
    hasResults,
    loadResults,
    loadHeatmap,
    getHeatmapImage,
    getByTile,
    select,
    setEnabled,
    setOpacity,
    setShowBbox,
    setColormap,
    clear
  }
}

export default useGradCAM
