import http from './http'
import type { ImageInfo, ImageUploadResponse, ImageListResponse } from '@/types'

export const uploadImage = async (file: File): Promise<ImageUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  
  return http.post('/api/images/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 300000
  })
}

export const getImage = async (imageId: string): Promise<ImageInfo> => {
  return http.get(`/api/images/${imageId}`)
}

export const getImageDzi = async (imageId: string): Promise<string> => {
  return http.get(`/api/images/${imageId}/dzi`)
}

export const getImageTile = async (
  imageId: string,
  level: number,
  x: number,
  y: number
): Promise<Blob> => {
  return http.get(`/api/images/${imageId}/tile/${level}/${x}_${y}`, {
    responseType: 'blob'
  })
}

export const listImages = async (params: { page: number; page_size: number }): Promise<ImageListResponse> => {
  return http.get('/api/images', { params })
}

export const downloadOriginal = async (imageId: string): Promise<Blob> => {
  return http.get(`/api/images/${imageId}/download`, {
    responseType: 'blob'
  })
}
