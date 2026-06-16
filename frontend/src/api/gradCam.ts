import http from './http'
import type {
  GradCAMResult,
  GradCAMHeatmapResponse,
  GradCAMListResponse
} from '@/types'

export const gradCamApi = {
  getResultsByTask(
    taskId: string,
    page: number = 1,
    pageSize: number = 100
  ): Promise<GradCAMListResponse> {
    return http.get(`/api/grad-cam/task/${taskId}`, {
      params: { page, page_size: pageSize }
    })
  },

  getResult(gradCamId: string): Promise<GradCAMResult> {
    return http.get(`/api/grad-cam/${gradCamId}`)
  },

  getHeatmap(gradCamId: string): Promise<GradCAMHeatmapResponse> {
    return http.get(`/api/grad-cam/${gradCamId}/heatmap`)
  },

  getHeatmapImage(
    gradCamId: string,
    colormap: string = 'jet'
  ): Promise<Blob> {
    return http.get(`/api/grad-cam/${gradCamId}/heatmap/image`, {
      params: { colormap },
      responseType: 'blob'
    })
  },

  getByTile(
    taskId: string,
    tileX: number,
    tileY: number
  ): Promise<GradCAMResult> {
    return http.get(`/api/grad-cam/task/${taskId}/tile/${tileX}/${tileY}`)
  }
}

export default gradCamApi
