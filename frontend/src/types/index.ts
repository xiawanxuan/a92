export type SubstrateClass = 'sediment' | 'rock' | 'coral' | 'man_made'

export interface SubstrateInfo {
  key: SubstrateClass
  name: string
  color: string
}

export const SUBSTRATE_TYPES: SubstrateInfo[] = [
  { key: 'sediment', name: '泥沙', color: '#f59e0b' },
  { key: 'rock', name: '岩石', color: '#6b7280' },
  { key: 'coral', name: '珊瑚', color: '#ec4899' },
  { key: 'man_made', name: '人工目标', color: '#3b82f6' }
]

export function getSubstrateInfo(key: SubstrateClass): SubstrateInfo {
  return SUBSTRATE_TYPES.find(s => s.key === key) || SUBSTRATE_TYPES[0]
}

export interface ImageInfo {
  id: string
  original_filename: string
  width: number
  height: number
  format: string
  file_size: number
  tile_size: number
  num_tiles_x: number
  num_tiles_y: number
  total_tiles: number
  minio_bucket: string
  minio_object: string
  dzi_bucket?: string
  dzi_object?: string
  upload_time: string
}

export interface ImageUploadResponse {
  id: string
  original_filename: string
  width: number
  height: number
  total_tiles: number
  message: string
}

export interface ImageListResponse {
  items: ImageInfo[]
  total: number
  page: number
  page_size: number
}

export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface ClassificationTask {
  id: string
  image_id: string
  status: TaskStatus
  progress: number
  processed_tiles: number
  total_tiles: number
  start_time: string
  end_time?: string
  error_message?: string
}

export interface ClassificationStartRequest {
  image_id: string
}

export interface TileClassification {
  tile_id: string
  tile_x: number
  tile_y: number
  pixel_x: number
  pixel_y: number
  predicted_class: SubstrateClass
  confidence: number
  is_corrected: boolean
  corrected_class?: SubstrateClass
  corrected_at?: string
  corrected_by?: string
}

export interface ClassificationResultsResponse {
  task_id: string
  status: TaskStatus
  total_tiles: number
  results: TileClassification[]
}

export interface HeatmapTile {
  tile_id: string
  tile_x: number
  tile_y: number
  pixel_x: number
  pixel_y: number
  predicted_class: SubstrateClass
  actual_class: SubstrateClass
  confidence: number
  is_corrected: boolean
}

export interface HeatmapDataResponse {
  task_id: string
  tile_size: number
  num_tiles_x: number
  num_tiles_y: number
  tile_data: HeatmapTile[]
}

export interface CorrectionRequest {
  new_class: SubstrateClass
  reason?: string
  operator: string
}

export interface CorrectionResponse {
  success: boolean
  tile_id: string
  original_class: SubstrateClass
  new_class: SubstrateClass
  message: string
}

export interface CorrectionRecord {
  id: string
  image_id: string
  task_id: string
  tile_id: string
  tile_x: number
  tile_y: number
  original_class: SubstrateClass
  new_class: SubstrateClass
  reason?: string
  operator: string
  created_at: string
}

export interface CorrectionListResponse {
  items: CorrectionRecord[]
  total: number
  page: number
  page_size: number
}

export interface TaskListResponse {
  items: ClassificationTask[]
  total: number
  page: number
  page_size: number
}

export interface ClassDistributionItem {
  count: number
  percentage: number
  avg_confidence: number
}

export interface StatsSummaryResponse {
  task_id: string
  total_tiles: number
  class_distribution: Record<SubstrateClass, ClassDistributionItem>
}

export interface ProfileRow {
  position: number
  sediment: number
  rock: number
  coral: number
  man_made: number
}

export interface ProfileDataResponse {
  task_id: string
  profile_data: ProfileRow[]
  image_width: number
  tile_size: number
}

export interface HeatmapSettings {
  opacity: number
  show_grid: boolean
  hidden_classes: SubstrateClass[]
}

export const TASK_STATUS_NAMES: Record<TaskStatus, string> = {
  pending: '等待中',
  processing: '处理中',
  completed: '已完成',
  failed: '失败'
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
  area_ratio: number
  avg_intensity: number
  max_intensity: number
  confidence: number
}

export interface GradCAMResult {
  id: string
  classification_id: string
  tile_id: string
  image_id: string
  task_id: string
  tile_x: number
  tile_y: number
  target_class: SubstrateClass
  confidence: number
  heatmap_width: number
  heatmap_height: number
  has_bbox: boolean
  bbox?: BoundingBox
  created_at: string
}

export interface GradCAMHeatmapResponse {
  id: string
  tile_x: number
  tile_y: number
  target_class: SubstrateClass
  confidence: number
  heatmap: number[][]
  bbox?: BoundingBox
}

export interface GradCAMListResponse {
  items: GradCAMResult[]
  total: number
  page: number
  page_size: number
}

export interface GradCAMOverlaySettings {
  enabled: boolean
  opacity: number
  show_bbox: boolean
  heatmap_colormap: 'jet' | 'hot' | 'viridis' | 'plasma'
}
