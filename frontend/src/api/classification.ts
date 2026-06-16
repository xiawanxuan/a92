import http from './http'
import type {
  ClassificationTask,
  ClassificationResultsResponse,
  CorrectionRequest,
  CorrectionResponse,
  CorrectionRecord,
  StatsSummaryResponse,
  ProfileDataResponse,
  HeatmapDataResponse,
  TaskListResponse,
  CorrectionListResponse,
  ClassificationStartRequest
} from '@/types'

export const startClassification = async (imageId: string): Promise<ClassificationTask> => {
  const request: ClassificationStartRequest = { image_id: imageId }
  return http.post('/api/classification/start', request)
}

export const getTaskStatus = async (taskId: string): Promise<ClassificationTask> => {
  return http.get(`/api/classification/${taskId}/status`)
}

export const getClassificationResults = async (taskId: string): Promise<ClassificationResultsResponse> => {
  return http.get(`/api/classification/${taskId}/results`)
}

export const getHeatmapData = async (taskId: string): Promise<HeatmapDataResponse> => {
  return http.get(`/api/classification/${taskId}/heatmap`)
}

export const correctTile = async (
  taskId: string,
  tileId: string,
  request: CorrectionRequest
): Promise<CorrectionResponse> => {
  return http.post(`/api/classification/${taskId}/tile/${tileId}/correct`, request)
}

export const listClassificationTasks = async (params: { page: number; page_size: number }): Promise<TaskListResponse> => {
  return http.get('/api/classification', { params })
}

export const listCorrections = async (params: { page: number; page_size: number }): Promise<CorrectionListResponse> => {
  return http.get('/api/classification/corrections', { params })
}

export const getStatsSummary = async (taskId: string): Promise<StatsSummaryResponse> => {
  return http.get(`/api/stats/${taskId}/summary`)
}

export const getProfileData = async (taskId: string): Promise<ProfileDataResponse> => {
  return http.get(`/api/stats/${taskId}/profile`)
}

export const exportReport = async (taskId: string): Promise<Blob> => {
  return http.get(`/api/classification/${taskId}/export`, {
    responseType: 'blob'
  })
}
