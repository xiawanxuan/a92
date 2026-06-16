<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElButton } from 'element-plus'
import { listCorrections } from '@/api/classification'
import { SUBSTRATE_TYPES, type CorrectionRecord } from '@/types'

const CLASS_NAMES: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.name
  return acc
}, {} as Record<string, string>)

const CLASS_COLORS: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.color
  return acc
}, {} as Record<string, string>)

const router = useRouter()

const corrections = ref<CorrectionRecord[]>([])
const loading = ref(false)

const loadData = async () => {
  loading.value = true
  try {
    const res = await listCorrections({ page: 1, page_size: 100 })
    corrections.value = res.items
  } catch (err) {
    console.error('加载数据失败:', err)
    ElMessage.error('加载修正记录失败')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getClassTag = (type: string) => {
  const color = CLASS_COLORS[type] || '#64748b'
  const name = CLASS_NAMES[type] || type
  return { color, name }
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="corrections-page min-h-screen bg-slate-900 p-6">
    <div class="max-w-7xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-white mb-1">人工修正记录</h1>
          <p class="text-slate-400">所有人工修正的分类结果将用于模型增量训练</p>
        </div>
        <ElButton type="primary" @click="goBack">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回分析
        </ElButton>
      </div>
      
      <div class="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div v-if="loading" class="flex items-center justify-center py-20">
          <div class="flex items-center gap-3 text-slate-400">
            <svg class="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            加载中...
          </div>
        </div>
        
        <div v-else-if="corrections.length === 0" class="text-center py-20">
          <svg class="w-16 h-16 mx-auto mb-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <p class="text-slate-400 text-lg">暂无修正记录</p>
          <p class="text-slate-500 text-sm mt-1">在分析界面中手动修正图块分类结果</p>
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-700/50">
              <tr>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">ID</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">图像ID</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">图块位置</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">原分类</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">新分类</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">修正原因</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">修正时间</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700">
              <tr 
                v-for="corr in corrections" 
                :key="corr.id"
                class="hover:bg-slate-700/30 transition-colors"
              >
                <td class="px-6 py-4 text-slate-300 font-mono text-xs">{{ corr.id }}</td>
                <td class="px-6 py-4 text-slate-300 font-mono text-xs">{{ corr.image_id }}</td>
                <td class="px-6 py-4 text-slate-300">
                  ({{ corr.tile_x }}, {{ corr.tile_y }})
                </td>
                <td class="px-6 py-4">
                  <span 
                    class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium text-white"
                    :style="{ backgroundColor: getClassTag(corr.original_class).color }"
                  >
                    {{ getClassTag(corr.original_class).name }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <span 
                    class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium text-white"
                    :style="{ backgroundColor: getClassTag(corr.new_class).color }"
                  >
                    {{ getClassTag(corr.new_class).name }}
                  </span>
                </td>
                <td class="px-6 py-4 text-slate-300 max-w-xs truncate" :title="corr.reason || ''">
                  {{ corr.reason || '-' }}
                </td>
                <td class="px-6 py-4 text-slate-300">{{ formatDate(corr.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.corrections-page {
  min-height: 100vh;
}
</style>
