import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ImageInfo, ImageUploadResponse, ImageListResponse } from '@/types'
import {
  uploadImage,
  getImage,
  getImageDzi,
  listImages,
  downloadOriginal
} from '@/api/image'
import { ElMessage } from 'element-plus'

export const useImageStore = defineStore('image', () => {
  const currentImage = ref<ImageInfo | null>(null)
  const imageList = ref<ImageInfo[]>([])
  const dziUrl = ref<string | null>(null)
  const uploading = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const uploadProgress = ref(0)

  const hasImage = computed(() => currentImage.value !== null)

  async function upload(file: File): Promise<ImageInfo> {
    uploading.value = true
    error.value = null
    uploadProgress.value = 0
    
    try {
      const response = await uploadImage(file)
      ElMessage.success(`上传成功：${response.original_filename}`)
      
      await loadImage(response.id)
      return currentImage.value!
    } catch (e: any) {
      error.value = e.message || '上传失败'
      ElMessage.error(error.value)
      throw e
    } finally {
      uploading.value = false
      uploadProgress.value = 0
    }
  }

  async function loadImage(imageId: string): Promise<ImageInfo> {
    loading.value = true
    error.value = null
    
    try {
      const image = await getImage(imageId)
      currentImage.value = image
      
      try {
        dziUrl.value = await getImageDzi(imageId)
      } catch (e) {
        console.warn('加载DZI失败:', e)
      }
      
      return image
    } catch (e: any) {
      error.value = e.message || '加载图像失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadImageList(page = 1, pageSize = 100): Promise<ImageInfo[]> {
    loading.value = true
    try {
      const response = await listImages({ page, page_size: pageSize })
      imageList.value = response.items
      return response.items
    } catch (e: any) {
      error.value = e.message || '加载图像列表失败'
      return []
    } finally {
      loading.value = false
    }
  }

  async function download(imageId: string): Promise<void> {
    try {
      const blob = await downloadOriginal(imageId)
      const image = imageList.value.find(img => img.id === imageId) || currentImage.value
      const filename = image?.original_filename || `image_${imageId}.tif`
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
      ElMessage.success('下载已开始')
    } catch (e: any) {
      error.value = e.message || '下载失败'
      ElMessage.error(error.value)
      throw e
    }
  }

  function clearCurrent() {
    currentImage.value = null
    dziUrl.value = null
    error.value = null
  }

  return {
    currentImage,
    imageList,
    dziUrl,
    uploading,
    loading,
    error,
    uploadProgress,
    hasImage,
    upload,
    loadImage,
    loadImageList,
    download,
    clearCurrent
  }
})
