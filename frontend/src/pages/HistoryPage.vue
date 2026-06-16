<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElButton } from 'element-plus'
import { listClassificationTasks } from '@/api/classification'
import { listImages } from '@/api/image'
import { TASK_STATUS_NAMES, SUBSTRATE_TYPES, type ClassificationTask, type ImageInfo } from '@/types'

const CLASS_NAMES: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.name
  return acc
}, {} as Record<string, string>)

const router = useRouter()

const tasks = ref<ClassificationTask[]>([])
const imagesMap = ref<Record<string, ImageInfo>>({})
const loading = ref(false)

const loadData = async () => {
  loading.value = true
  try {
    const [tasksRes, imagesRes] = await Promise.all([
      listClassificationTasks({ page: 1, page_size: 50 }),
      listImages({ page: 1, page_size: 100 })
    ])
    
    tasks.value = tasksRes.items
    imagesRes.items.forEach(img => {
      imagesMap.value[img.id] = img
    })
  } catch (err) {
    console.error('加载数据失败:', err)
    ElMessage.error('加载历史记录失败')
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

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-500',
    processing: 'bg-blue-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500'
  }
  return colors[status] || 'bg-gray-500'
}

const openTask = (task: ClassificationTask) => {
  router.push(`/?image_id=${task.image_id}&task_id=${task.id}`)
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="history-page min-h-screen bg-slate-900 p-6">
    <div class="max-w-7xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-white mb-1">历史分析任务</h1>
          <p class="text-slate-400">查看所有声呐图像分析任务记录</p>
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
        
        <div v-else-if="tasks.length === 0" class="text-center py-20">
          <svg class="w-16 h-16 mx-auto mb-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p class="text-slate-400 text-lg">暂无分析任务</p>
          <p class="text-slate-500 text-sm mt-1">上传声呐图像开始第一次分析</p>
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-700/50">
              <tr>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">图像名称</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">分辨率</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">图块数量</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">状态</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">创建时间</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">完成时间</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-slate-300">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700">
              <tr 
                v-for="task in tasks" 
                :key="task.id"
                class="hover:bg-slate-700/30 transition-colors"
              >
                <td class="px-6 py-4">
                  <div class="text-white font-medium">
                    {{ imagesMap[task.image_id]?.original_filename || `图像 #${task.image_id}` }}
                  </div>
                  <div class="text-slate-400 text-sm">任务 #{{ task.id }}</div>
                </td>
                <td class="px-6 py-4 text-slate-300">
                  {{ imagesMap[task.image_id]?.width }} × {{ imagesMap[task.image_id]?.height }}
                </td>
                <td class="px-6 py-4 text-slate-300">{{ task.total_tiles }}</td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <span :class="[getStatusColor(task.status), 'w-2 h-2 rounded-full']"></span>
                    <span class="text-slate-300">{{ TASK_STATUS_NAMES[task.status as keyof typeof TASK_STATUS_NAMES] || task.status }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 text-slate-300">{{ formatDate(task.start_time) }}</td>
                <td class="px-6 py-4 text-slate-300">
                  {{ task.end_time ? formatDate(task.end_time) : '-' }}
                </td>
                <td class="px-6 py-4">
                  <ElButton 
                    type="primary" 
                    size="small" 
                    @click="openTask(task)"
                    :disabled="task.status !== 'completed'"
                  >
                    查看
                  </ElButton>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  min-height: 100vh;
}
</style>
