import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ClassificationTask,
  ClassificationResultsResponse,
  StatsSummaryResponse,
  ProfileDataResponse,
  HeatmapDataResponse,
  CorrectionRequest,
  CorrectionResponse,
  CorrectionRecord,
  TileClassification,
  HeatmapSettings,
  GradCAMResult,
  GradCAMHeatmapResponse,
  GradCAMListResponse,
  GradCAMOverlaySettings
} from '@/types'
import {
  startClassification,
  getTaskStatus,
  getClassificationResults,
  getHeatmapData,
  correctTile,
  listClassificationTasks,
  listCorrections,
  getStatsSummary,
  getProfileData
} from '@/api/classification'
import { gradCamApi } from '@/api/gradCam'
import { ElMessage } from 'element-plus'

export const useClassificationStore = defineStore('classification', () => {
  const currentTask = ref<ClassificationTask | null>(null)
  const classificationResults = ref<ClassificationResultsResponse | null>(null)
  const statsSummary = ref<StatsSummaryResponse | null>(null)
  const profileData = ref<ProfileDataResponse | null>(null)
  const heatmapData = ref<HeatmapDataResponse | null>(null)
  const taskList = ref<ClassificationTask[]>([])
  const correctionRecords = ref<CorrectionRecord[]>([])
  const loading = ref(false)
  const processing = ref(false)
  const error = ref<string | null>(null)
  const progressTimer = ref<number | null>(null)

  const heatmapSettings = ref<HeatmapSettings>({
    opacity: 0.6,
    show_grid: false,
    hidden_classes: []
  })

  const selectedTile = ref<TileClassification | null>(null)
  const correctionMode = ref(false)

  const gradCamResults = ref<GradCAMResult[]>([])
  const gradCamHeatmaps = ref<Map<string, GradCAMHeatmapResponse>>(new Map())
  const selectedGradCam = ref<GradCAMResult | null>(null)
  const gradCamLoading = ref(false)

  const gradCamOverlaySettings = ref<GradCAMOverlaySettings>({
    enabled: false,
    opacity: 0.7,
    show_bbox: true,
    heatmap_colormap: 'jet'
  })

  const hasGradCamResults = computed(() => gradCamResults.value.length > 0)

  const isProcessing = computed(() =>
    currentTask.value?.status === 'processing' ||
    currentTask.value?.status === 'pending'
  )

  const isCompleted = computed(() =>
    currentTask.value?.status === 'completed'
  )

  const progressPercent = computed(() => currentTask.value?.progress ?? 0)

  const progressStatus = computed(() => {
    if (!currentTask.value) return ''
    const status = currentTask.value.status
    const statusMap: Record<string, string> = {
      pending: '准备中...',
      processing: '推理中...',
      completed: '完成',
      failed: '失败'
    }
    return statusMap[status] || status
  })

  async function start(imageId: string): Promise<ClassificationTask> {
    processing.value = true
    error.value = null
    try {
      currentTask.value = await startClassification(imageId)
      startProgressPolling(currentTask.value.id)
      return currentTask.value
    } catch (e: any) {
      error.value = e.message || '启动分类失败'
      ElMessage.error(error.value)
      throw e
    } finally {
      processing.value = false
    }
  }

  function startProgressPolling(taskId: string) {
    stopProgressPolling()
    progressTimer.value = window.setInterval(async () => {
      try {
        const status = await getTaskStatus(taskId)
        currentTask.value = status

        if (status.status === 'completed' || status.status === 'failed') {
          stopProgressPolling()
          if (status.status === 'completed') {
            await loadAllData(taskId)
            ElMessage.success('分类完成！')
          } else if (status.status === 'failed') {
            ElMessage.error(`分类失败：${status.error_message || '未知错误'}`)
          }
        }
      } catch (e) {
        console.error('Progress polling error:', e)
      }
    }, 2000)
  }

  function stopProgressPolling() {
    if (progressTimer.value) {
      clearInterval(progressTimer.value)
      progressTimer.value = null
    }
  }

  function stopPolling() {
    stopProgressPolling()
  }

  async function loadAllData(taskId: string) {
    loading.value = true
    try {
      const [results, heatmap, stats, profile] = await Promise.all([
        getClassificationResults(taskId),
        getHeatmapData(taskId),
        getStatsSummary(taskId),
        getProfileData(taskId)
      ])
      classificationResults.value = results
      heatmapData.value = heatmap
      statsSummary.value = stats
      profileData.value = profile

      await loadGradCamResults(taskId)
    } catch (e: any) {
      error.value = e.message || '加载数据失败'
      ElMessage.error(error.value)
    } finally {
      loading.value = false
    }
  }

  async function loadGradCamResults(taskId: string, page = 1, pageSize = 200) {
    gradCamLoading.value = true
    try {
      const response = await gradCamApi.getResultsByTask(taskId, page, pageSize)
      gradCamResults.value = response.items
    } catch (e: any) {
      console.warn('加载 Grad-CAM 结果失败:', e.message)
      gradCamResults.value = []
    } finally {
      gradCamLoading.value = false
    }
  }

  async function loadGradCamHeatmap(gradCamId: string): Promise<GradCAMHeatmapResponse | null> {
    try {
      const existing = gradCamHeatmaps.value.get(gradCamId)
      if (existing) return existing

      const heatmap = await gradCamApi.getHeatmap(gradCamId)
      gradCamHeatmaps.value.set(gradCamId, heatmap)
      return heatmap
    } catch (e: any) {
      console.error('加载 Grad-CAM 热力图失败:', e.message)
      return null
    }
  }

  async function getGradCamHeatmapImage(gradCamId: string, colormap = 'jet'): Promise<string | null> {
    try {
      const blob = await gradCamApi.getHeatmapImage(gradCamId, colormap)
      return URL.createObjectURL(blob)
    } catch (e: any) {
      console.error('加载 Grad-CAM 热力图图片失败:', e.message)
      return null
    }
  }

  function selectGradCam(gradCam: GradCAMResult | null) {
    selectedGradCam.value = gradCam
  }

  function setGradCamOverlayEnabled(value: boolean) {
    gradCamOverlaySettings.value.enabled = value
  }

  function setGradCamOpacity(value: number) {
    gradCamOverlaySettings.value.opacity = Math.max(0, Math.min(1, value))
  }

  function setGradCamShowBbox(value: boolean) {
    gradCamOverlaySettings.value.show_bbox = value
  }

  function setGradCamColormap(value: 'jet' | 'hot' | 'viridis' | 'plasma') {
    gradCamOverlaySettings.value.heatmap_colormap = value
  }

  async function correct(
    taskId: string,
    tileId: string,
    request: CorrectionRequest
  ): Promise<CorrectionResponse> {
    try {
      const response = await correctTile(taskId, tileId, request)

      if (classificationResults.value) {
        const tile = classificationResults.value.results.find(t => t.tile_id === tileId)
        if (tile) {
          tile.is_corrected = true
          tile.corrected_class = request.new_class
          tile.corrected_at = new Date().toISOString()
          tile.corrected_by = request.operator
        }
      }

      if (heatmapData.value) {
        const tile = heatmapData.value.tile_data.find(t => t.tile_id === tileId)
        if (tile) {
          tile.actual_class = request.new_class
          tile.is_corrected = true
        }
      }

      await Promise.all([
        getStatsSummary(taskId).then(s => { statsSummary.value = s }),
        getProfileData(taskId).then(p => { profileData.value = p })
      ])

      ElMessage.success('修正已保存')
      return response
    } catch (e: any) {
      error.value = e.message || '修正失败'
      ElMessage.error(error.value)
      throw e
    }
  }

  async function fetchTaskList(page = 1, pageSize = 50) {
    loading.value = true
    try {
      const res = await listClassificationTasks({ page, page_size: pageSize })
      taskList.value = res.items
    } catch (e: any) {
      error.value = e.message || '加载任务列表失败'
      ElMessage.error(error.value)
    } finally {
      loading.value = false
    }
  }

  async function fetchCorrectionRecords(page = 1, pageSize = 100) {
    loading.value = true
    try {
      const res = await listCorrections({ page, page_size: pageSize })
      correctionRecords.value = res.items
    } catch (e: any) {
      error.value = e.message || '加载修正记录失败'
      ElMessage.error(error.value)
    } finally {
      loading.value = false
    }
  }

  function toggleClassVisibility(classType: string) {
    const idx = heatmapSettings.value.hidden_classes.indexOf(classType as any)
    if (idx >= 0) {
      heatmapSettings.value.hidden_classes.splice(idx, 1)
    } else {
      heatmapSettings.value.hidden_classes.push(classType as any)
    }
  }

  function setHeatmapOpacity(value: number) {
    heatmapSettings.value.opacity = Math.max(0, Math.min(1, value))
  }

  function setShowGrid(value: boolean) {
    heatmapSettings.value.show_grid = value
  }

  function selectTile(tile: TileClassification | null) {
    selectedTile.value = tile
  }

  function setCorrectionMode(value: boolean) {
    correctionMode.value = value
    if (!value) {
      selectedTile.value = null
    }
  }

  function clearAll() {
    stopProgressPolling()
    currentTask.value = null
    classificationResults.value = null
    statsSummary.value = null
    profileData.value = null
    heatmapData.value = null
    selectedTile.value = null
    correctionMode.value = false
    gradCamResults.value = []
    gradCamHeatmaps.value.clear()
    selectedGradCam.value = null
    gradCamOverlaySettings.value = {
      enabled: false,
      opacity: 0.7,
      show_bbox: true,
      heatmap_colormap: 'jet'
    }
    error.value = null
  }

  return {
    currentTask,
    classificationResults,
    statsSummary,
    profileData,
    heatmapData,
    taskList,
    correctionRecords,
    loading,
    processing,
    error,
    heatmapSettings,
    selectedTile,
    correctionMode,
    gradCamResults,
    gradCamHeatmaps,
    selectedGradCam,
    gradCamLoading,
    gradCamOverlaySettings,
    isProcessing,
    isCompleted,
    progressPercent,
    progressStatus,
    hasGradCamResults,
    start,
    loadAllData,
    correct,
    fetchTaskList,
    fetchCorrectionRecords,
    toggleClassVisibility,
    setHeatmapOpacity,
    setShowGrid,
    selectTile,
    setCorrectionMode,
    loadGradCamResults,
    loadGradCamHeatmap,
    getGradCamHeatmapImage,
    selectGradCam,
    setGradCamOverlayEnabled,
    setGradCamOpacity,
    setGradCamShowBbox,
    setGradCamColormap,
    clearAll,
    stopProgressPolling,
    stopPolling
  }
})
