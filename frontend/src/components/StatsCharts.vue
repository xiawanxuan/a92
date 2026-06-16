<script setup lang="ts">
import { ref, watch, onMounted, computed, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { useClassificationStore } from '@/stores/classificationStore'
import type { SubstrateClass } from '@/types'
import { SUBSTRATE_TYPES } from '@/types'

const CLASS_NAMES: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.name
  return acc
}, {} as Record<string, string>)

const CLASS_COLORS: Record<string, string> = SUBSTRATE_TYPES.reduce((acc, s) => {
  acc[s.key] = s.color
  return acc
}, {} as Record<string, string>)

const CLASS_KEYS: SubstrateClass[] = ['sediment', 'rock', 'coral', 'man_made']

const classificationStore = useClassificationStore()

const pieChartRef = ref<HTMLDivElement | null>(null)
const lineChartRef = ref<HTMLDivElement | null>(null)

let pieChart: echarts.ECharts | null = null
let lineChart: echarts.ECharts | null = null

const hasStats = computed(() => {
  return classificationStore.statsSummary && classificationStore.statsSummary.total_tiles > 0
})

const initPieChart = () => {
  if (!pieChartRef.value) return
  
  pieChart = echarts.init(pieChartRef.value)
  
  const option: echarts.EChartsOption = {
    title: {
      text: '底质类型占比',
      left: 'center',
      textStyle: {
        color: '#e2e8f0',
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 块 ({d}%)',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    series: [
      {
        name: '底质类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#0f172a',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          color: '#e2e8f0'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        data: []
      }
    ]
  }
  
  pieChart.setOption(option)
}

const initLineChart = () => {
  if (!lineChartRef.value) return
  
  lineChart = echarts.init(lineChartRef.value)
  
  const option: echarts.EChartsOption = {
    title: {
      text: '沿测线方向类别分布',
      left: 'center',
      textStyle: {
        color: '#e2e8f0',
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    legend: {
      data: [],
      textStyle: {
        color: '#e2e8f0'
      },
      top: 25
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: [],
      axisLabel: {
        color: '#94a3b8'
      },
      axisLine: {
        lineStyle: {
          color: '#334155'
        }
      },
      name: '测线位置 (像素)',
      nameTextStyle: {
        color: '#94a3b8'
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#94a3b8',
        formatter: '{value}%'
      },
      axisLine: {
        lineStyle: {
          color: '#334155'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#1e293b'
        }
      },
      max: 100
    },
    series: []
  }
  
  lineChart.setOption(option)
}

const updatePieChart = () => {
  if (!pieChart || !classificationStore.statsSummary) return
  
  const classDist = classificationStore.statsSummary.class_distribution
  const pieData = Object.entries(classDist).map(([type, stats]) => ({
    value: stats.count,
    name: CLASS_NAMES[type],
    itemStyle: {
      color: CLASS_COLORS[type]
    }
  })).filter(item => item.value > 0)
  
  pieChart.setOption({
    series: [{
      data: pieData
    }]
  })
}

const updateLineChart = () => {
  if (!lineChart || !classificationStore.profileData) return
  
  const profileData = classificationStore.profileData.profile_data
  
  const series = CLASS_KEYS.map(type => {
    const color = CLASS_COLORS[type]
    const data = profileData.map(row => Math.round(row[type]))
    
    return {
      name: CLASS_NAMES[type],
      type: 'line',
      smooth: true,
      data: data,
      lineStyle: {
        color: color,
        width: 2
      },
      itemStyle: {
        color: color
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: color + '60' },
          { offset: 1, color: color + '10' }
        ])
      }
    }
  })
  
  lineChart.setOption({
    legend: {
      data: CLASS_KEYS.map(t => CLASS_NAMES[t])
    },
    xAxis: {
      data: profileData.map(row => row.position.toFixed(0))
    },
    series: series
  })
}

const handleResize = () => {
  pieChart?.resize()
  lineChart?.resize()
}

watch(() => classificationStore.statsSummary, () => {
  updatePieChart()
}, { deep: true })

watch(() => classificationStore.profileData, () => {
  updateLineChart()
}, { deep: true })

onMounted(() => {
  initPieChart()
  initLineChart()
  window.addEventListener('resize', handleResize)
  
  if (hasStats.value) {
    updatePieChart()
    updateLineChart()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
  lineChart?.dispose()
})
</script>

<template>
  <div class="stats-charts h-full w-full flex gap-4">
    <div 
      v-if="hasStats"
      class="pie-chart flex-1 bg-slate-800/50 rounded-lg border border-slate-700"
    >
      <div ref="pieChartRef" class="w-full h-full"></div>
    </div>
    
    <div 
      v-if="hasStats"
      class="line-chart flex-1 bg-slate-800/50 rounded-lg border border-slate-700"
    >
      <div ref="lineChartRef" class="w-full h-full"></div>
    </div>
    
    <div 
      v-if="!hasStats"
      class="flex-1 flex items-center justify-center bg-slate-800/30 rounded-lg border border-slate-700 border-dashed"
    >
      <div class="text-center text-slate-400">
        <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p>完成分类后将显示统计图表</p>
        <p class="text-sm mt-1 opacity-70">包含类别占比饼图和沿测线分布折线图</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-charts {
  min-height: 280px;
}

.pie-chart,
.line-chart {
  min-height: 260px;
}
</style>
