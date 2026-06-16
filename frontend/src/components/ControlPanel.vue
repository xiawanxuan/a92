<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useClassificationStore } from '@/stores/classificationStore'
import { ElMessage } from 'element-plus'
import type { SubstrateClass, TileClassification } from '@/types'
import { SUBSTRATE_TYPES } from '@/types'

const classificationStore = useClassificationStore()

const correctionReason = ref('')
const correctionClass = ref<string | null>(null)

const heatmapOpacity = computed(() => classificationStore.heatmapSettings.opacity)
const hiddenClasses = computed(() => new Set(classificationStore.heatmapSettings.hidden_classes))
const showTileGrid = computed(() => classificationStore.heatmapSettings.show_grid)
const selectedTile = computed(() => classificationStore.selectedTile)
const isCompleted = computed(() => classificationStore.isCompleted)
const currentTask = computed(() => classificationStore.currentTask)
const correctionMode = computed(() => classificationStore.correctionMode)

const gradCamEnabled = computed(() => classificationStore.gradCamOverlaySettings.enabled)
const gradCamOpacity = computed(() => classificationStore.gradCamOverlaySettings.opacity)
const gradCamShowBbox = computed(() => classificationStore.gradCamOverlaySettings.show_bbox)
const gradCamColormap = computed(() => classificationStore.gradCamOverlaySettings.heatmap_colormap)
const hasGradCamResults = computed(() => classificationStore.hasGradCamResults)
const selectedGradCam = computed(() => classificationStore.selectedGradCam)
const gradCamResults = computed(() => classificationStore.gradCamResults)

const colormapOptions = [
  { value: 'jet', label: 'Jet' },
  { value: 'hot', label: 'Hot' },
  { value: 'viridis', label: 'Viridis' },
  { value: 'plasma', label: 'Plasma' }
]

const CLASS_NAMES: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.name
  return acc
}, {} as Record<string, string>)

const CLASS_COLORS: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.color
  return acc
}, {} as Record<string, string>)

const classList = SUBSTRATE_TYPES.map(s => ({
  type: s.key,
  name: s.name
}))

function toggleClassVisibility(classType: string) {
  classificationStore.toggleClassVisibility(classType)
}

function handleOpacityChange(event: Event) {
  const target = event.target as HTMLInputElement
  classificationStore.setHeatmapOpacity(parseFloat(target.value))
}

function toggleGrid() {
  classificationStore.setShowGrid(!classificationStore.heatmapSettings.show_grid)
}

function toggleGradCam() {
  classificationStore.setGradCamOverlayEnabled(!gradCamEnabled.value)
}

function handleGradCamOpacityChange(event: Event) {
  const target = event.target as HTMLInputElement
  classificationStore.setGradCamOpacity(parseFloat(target.value))
}

function toggleGradCamBbox() {
  classificationStore.setGradCamShowBbox(!gradCamShowBbox.value)
}

function handleColormapChange(value: string) {
  classificationStore.setGradCamColormap(value as any)
}

function getEffectiveClass(tile: TileClassification): SubstrateClass {
  return tile.is_corrected && tile.corrected_class
    ? tile.corrected_class
    : tile.predicted_class
}

function enterCorrectionMode() {
  if (!selectedTile.value) {
    ElMessage.warning('请先选择一个图块')
    return
  }
  classificationStore.setCorrectionMode(true)
  correctionClass.value = getEffectiveClass(selectedTile.value)
  correctionReason.value = ''
}

function cancelCorrection() {
  classificationStore.setCorrectionMode(false)
  correctionClass.value = null
  correctionReason.value = ''
}

async function confirmCorrection() {
  if (!selectedTile.value || !correctionClass.value || !currentTask.value) return

  try {
    await classificationStore.correct(
      currentTask.value.id,
      selectedTile.value.tile_id,
      {
        new_class: correctionClass.value as SubstrateClass,
        reason: correctionReason.value,
        operator: 'current_user'
      }
    )
    classificationStore.setCorrectionMode(false)
    correctionClass.value = null
    correctionReason.value = ''
  } catch (error: any) {
    ElMessage.error(error.message || '修正失败')
  }
}

watch(selectedTile, (tile) => {
  if (!tile && correctionMode.value) {
    cancelCorrection()
  }
})
</script>

<template>
  <div class="control-panel w-full h-full bg-slate-900/95 border-l border-slate-700 flex flex-col overflow-hidden">
    <div class="p-4 border-b border-slate-700">
      <h2 class="text-white font-mono text-lg font-bold flex items-center gap-2">
        <svg class="w-5 h-5 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
        </svg>
        控制面板
      </h2>
    </div>

    <div class="flex-1 overflow-y-auto p-4 space-y-6">
      <div v-if="!isCompleted" class="text-center py-8">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-800 flex items-center justify-center">
          <svg class="w-8 h-8 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="text-slate-400">上传图像并开始分类以查看结果</p>
      </div>

      <template v-else>
        <div class="space-y-4">
          <h3 class="text-slate-300 text-sm font-medium flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            分类图例
          </h3>

          <div class="space-y-2">
            <div
              v-for="cls in classList"
              :key="cls.type"
              class="flex items-center justify-between p-2 rounded-lg transition-all cursor-pointer hover:bg-slate-800/50"
              @click="toggleClassVisibility(cls.type)"
            >
              <div class="flex items-center gap-3">
                <div
                  class="w-6 h-6 rounded-md shadow-md"
                  :style="{ backgroundColor: CLASS_COLORS[cls.type] }"
                ></div>
                <span
                  class="text-sm transition-colors"
                  :class="hiddenClasses.has(cls.type) ? 'text-slate-500 line-through' : 'text-white'"
                >
                  {{ cls.name }}
                </span>
              </div>
              <svg 
                v-if="!hiddenClasses.has(cls.type)"
                class="w-4 h-4 text-slate-400" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <svg 
                v-else
                class="w-4 h-4 text-slate-600" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <h3 class="text-slate-300 text-sm font-medium flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            热力图设置
          </h3>

          <div class="space-y-3">
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-slate-400 text-sm">透明度</span>
                <span class="text-cyan-400 font-mono text-sm">{{ (heatmapOpacity * 100).toFixed(0) }}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                :value="heatmapOpacity"
                class="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                @input="handleOpacityChange"
              />
            </div>

            <button
              class="w-full flex items-center justify-between p-3 rounded-lg border transition-all"
              :class="showTileGrid
                ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400'
                : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:border-slate-600'"
              @click="toggleGrid"
            >
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
                <span class="text-sm">显示图块网格</span>
              </div>
              <div
                class="w-4 h-4 rounded flex items-center justify-center"
                :class="showTileGrid ? 'bg-cyan-500' : 'bg-slate-700'"
              >
                <svg v-if="showTileGrid" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </button>
          </div>
        </div>

        <div v-if="hasGradCamResults" class="space-y-4">
          <h3 class="text-slate-300 text-sm font-medium flex items-center gap-2">
            <svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            目标定位 (Grad-CAM)
            <span class="ml-auto text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400">
              {{ gradCamResults.length }} 处
            </span>
          </h3>

          <div class="space-y-3">
            <button
              class="w-full flex items-center justify-between p-3 rounded-lg border transition-all"
              :class="gradCamEnabled
                ? 'border-red-500 bg-red-500/10 text-red-400'
                : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:border-slate-600'"
              @click="toggleGradCam"
            >
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <span class="text-sm">显示目标热力图</span>
              </div>
              <div
                class="w-4 h-4 rounded flex items-center justify-center"
                :class="gradCamEnabled ? 'bg-red-500' : 'bg-slate-700'"
              >
                <svg v-if="gradCamEnabled" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </button>

            <template v-if="gradCamEnabled">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <span class="text-slate-400 text-sm">热力图透明度</span>
                  <span class="text-red-400 font-mono text-sm">{{ (gradCamOpacity * 100).toFixed(0) }}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  :value="gradCamOpacity"
                  class="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                  @input="handleGradCamOpacityChange"
                />
              </div>

              <div>
                <label class="text-slate-400 text-sm mb-2 block">配色方案</label>
                <div class="grid grid-cols-4 gap-2">
                  <button
                    v-for="opt in colormapOptions"
                    :key="opt.value"
                    class="py-2 px-2 rounded border text-xs transition-all"
                    :class="gradCamColormap === opt.value
                      ? 'border-red-500 bg-red-500/10 text-red-400'
                      : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:border-slate-600'"
                    @click="handleColormapChange(opt.value)"
                  >
                    {{ opt.label }}
                  </button>
                </div>
              </div>

              <button
                class="w-full flex items-center justify-between p-3 rounded-lg border transition-all"
                :class="gradCamShowBbox
                  ? 'border-red-500 bg-red-500/10 text-red-400'
                  : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:border-slate-600'"
                @click="toggleGradCamBbox"
              >
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                  </svg>
                  <span class="text-sm">显示边界框</span>
                </div>
                <div
                  class="w-4 h-4 rounded flex items-center justify-center"
                  :class="gradCamShowBbox ? 'bg-red-500' : 'bg-slate-700'"
                >
                  <svg v-if="gradCamShowBbox" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </button>
            </template>

            <div v-if="selectedGradCam" class="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
              <div class="text-red-400 text-sm font-medium mb-2">已选目标</div>
              <div class="text-slate-400 text-xs space-y-1">
                <p>位置: ({{ selectedGradCam.tile_x }}, {{ selectedGradCam.tile_y }})</p>
                <p>置信度: {{ (selectedGradCam.confidence * 100).toFixed(1) }}%</p>
                <p v-if="selectedGradCam.bbox">
                  尺寸: {{ selectedGradCam.bbox.width.toFixed(0) }} × {{ selectedGradCam.bbox.height.toFixed(0) }}
                </p>
                <p v-if="selectedGradCam.bbox">
                  面积占比: {{ (selectedGradCam.bbox.area_ratio * 100).toFixed(1) }}%
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <h3 class="text-slate-300 text-sm font-medium flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            人工修正
          </h3>

          <div
            v-if="!selectedTile"
            class="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50 text-center"
          >
            <p class="text-slate-500 text-sm">点击图像中的图块进行选择</p>
          </div>

          <div v-else class="space-y-3">
            <div class="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
              <div class="flex items-center justify-between mb-3">
                <span class="text-slate-400 text-sm">已选图块</span>
                <span class="text-white font-mono text-sm">
                  ({{ selectedTile.tile_x }}, {{ selectedTile.tile_y }})
                </span>
              </div>

              <div class="flex items-center gap-3 mb-2">
                <div
                  class="w-8 h-8 rounded-lg shadow-md"
                  :style="{ backgroundColor: CLASS_COLORS[getEffectiveClass(selectedTile)] }"
                ></div>
                <div>
                  <p class="text-white font-medium">{{ CLASS_NAMES[getEffectiveClass(selectedTile)] }}</p>
                  <p class="text-slate-400 text-xs">
                    置信度: {{ (selectedTile.confidence * 100).toFixed(1) }}%
                  </p>
                </div>
              </div>

              <div v-if="selectedTile.is_corrected" class="mt-2 px-2 py-1 rounded bg-amber-500/20 text-amber-400 text-xs">
                已修正 · {{ selectedTile.corrected_by }}
              </div>
            </div>

            <div v-if="!correctionMode">
              <button
                class="w-full py-3 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-white font-medium hover:shadow-lg hover:shadow-amber-500/30 transition-all"
                @click="enterCorrectionMode"
              >
                <div class="flex items-center justify-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  <span>修正分类结果</span>
                </div>
              </button>
            </div>

            <div v-else class="space-y-3">
              <div>
                <label class="text-slate-400 text-sm mb-2 block">修正为</label>
                <div class="grid grid-cols-2 gap-2">
                  <button
                    v-for="cls in classList"
                    :key="cls.type"
                    class="p-3 rounded-lg border transition-all text-left"
                    :class="correctionClass === cls.type
                      ? 'border-cyan-500 bg-cyan-500/10'
                      : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'"
                    @click="correctionClass = cls.type"
                  >
                    <div class="flex items-center gap-2">
                      <div
                        class="w-4 h-4 rounded"
                        :style="{ backgroundColor: CLASS_COLORS[cls.type] }"
                      ></div>
                      <span
                        class="text-sm"
                        :class="correctionClass === cls.type ? 'text-cyan-400' : 'text-white'"
                      >
                        {{ cls.name }}
                      </span>
                    </div>
                  </button>
                </div>
              </div>

              <div>
                <label class="text-slate-400 text-sm mb-2 block">修正原因 (可选)</label>
                <textarea
                  v-model="correctionReason"
                  placeholder="请输入修正原因..."
                  class="w-full h-20 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700 text-white text-sm resize-none focus:outline-none focus:border-cyan-500 transition-colors"
                ></textarea>
              </div>

              <div class="flex gap-2">
                <button
                  class="flex-1 py-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors flex items-center justify-center gap-2"
                  @click="cancelCorrection"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  取消
                </button>
                <button
                  class="flex-1 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-green-600 text-white hover:shadow-lg transition-all flex items-center justify-center gap-2"
                  @click="confirmCorrection"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  确认
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div class="p-4 border-t border-slate-700">
      <div class="text-slate-500 text-xs text-center">
        <p>分类结果仅供参考</p>
        <p>建议结合专业知识进行判断</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.4);
  transition: transform 0.2s;
}

input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

input[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.4);
}
</style>
