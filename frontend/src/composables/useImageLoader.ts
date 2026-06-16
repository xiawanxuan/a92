import { ref, onUnmounted } from 'vue'
import type { ImageInfo } from '@/types'
import { getImageDzi } from '@/api/image'

export function useImageLoader() {
  const viewer = ref<any>(null)
  const container = ref<HTMLElement | null>(null)
  const isReady = ref(false)
  const zoom = ref(1)
  const center = ref({ x: 0, y: 0 })
  const cursorPosition = ref({ x: 0, y: 0, imageX: 0, imageY: 0 })

  async function initViewer(imageData: ImageInfo, containerEl: HTMLElement, dziUrl: string) {
    return new Promise<void>((resolve, reject) => {
      import('openseadragon').then(OSD => {
        container.value = containerEl

        if (viewer.value) {
          viewer.value.destroy()
        }

        viewer.value = new OSD.default({
          element: containerEl,
          prefixUrl: 'https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/images/',
          tileSources: dziUrl,
          showNavigator: true,
          navigatorPosition: 'BOTTOM_RIGHT',
          navigatorSizeRatio: 0.15,
          animationTime: 0.2,
          blendTime: 0.1,
          constrainDuringPan: true,
          visibilityRatio: 1,
          minZoomLevel: 0.1,
          maxZoomLevel: 20,
          defaultZoomLevel: 1,
          tileLoadingSuccessTimeout: 10000
        })

        viewer.value.addHandler('open', () => {
          isReady.value = true
          resolve()
        })

        viewer.value.addHandler('error', (event: any) => {
          reject(new Error(event.message || 'Failed to load image'))
        })

        viewer.value.addHandler('zoom', (event: any) => {
          zoom.value = event.zoom
        })

        viewer.value.addHandler('update-viewport', () => {
          if (!viewer.value) return
          const vp = viewer.value.viewport
          const centerPt = vp.getCenter()
          center.value = { x: centerPt.x, y: centerPt.y }
        })

        viewer.value.addHandler('canvas-click', (event: any) => {
          const webPoint = event.position
          const imagePoint = viewer.value.viewport.pointFromPixel(webPoint)
          cursorPosition.value = {
            x: webPoint.x,
            y: webPoint.y,
            imageX: imagePoint.x * imageData.width,
            imageY: imagePoint.y * imageData.height
          }
        })
      }).catch(reject)
    })
  }

  function zoomTo(factor: number) {
    if (viewer.value) {
      viewer.value.viewport.zoomBy(factor)
    }
  }

  function zoomToLevel(level: number) {
    if (viewer.value) {
      viewer.value.viewport.zoomTo(level)
    }
  }

  function resetView() {
    if (viewer.value) {
      viewer.value.viewport.goHome()
    }
  }

  function screenToImageCoordinates(screenX: number, screenY: number, imageData: ImageInfo) {
    if (!viewer.value) return null
    const webPoint = new (viewer.value as any).Point(screenX, screenY)
    const imagePoint = viewer.value.viewport.pointFromPixel(webPoint)
    return {
      x: imagePoint.x * imageData.width,
      y: imagePoint.y * imageData.height
    }
  }

  function imageToScreenCoordinates(imageX: number, imageY: number, imageData: ImageInfo) {
    if (!viewer.value) return null
    const imagePoint = new (viewer.value as any).Point(
      imageX / imageData.width,
      imageY / imageData.height
    )
    const screenPoint = viewer.value.viewport.pointToPixel(imagePoint)
    return {
      x: screenPoint.x,
      y: screenPoint.y
    }
  }

  function addOverlay(element: HTMLElement, x: number, y: number, width: number, height: number, imageData: ImageInfo) {
    if (!viewer.value) return
    const rect = new (viewer.value as any).Rect(
      x / imageData.width,
      y / imageData.height,
      width / imageData.width,
      height / imageData.height
    )
    viewer.value.addOverlay(element, rect)
  }

  function updateOverlay(element: HTMLElement, x: number, y: number, width: number, height: number, imageData: ImageInfo) {
    if (!viewer.value) return
    const rect = new (viewer.value as any).Rect(
      x / imageData.width,
      y / imageData.height,
      width / imageData.width,
      height / imageData.height
    )
    viewer.value.updateOverlay(element, rect)
  }

  function removeOverlay(element: HTMLElement) {
    if (viewer.value) {
      viewer.value.removeOverlay(element)
    }
  }

  function forceRedraw() {
    if (viewer.value) {
      viewer.value.forceRedraw()
    }
  }

  function destroy() {
    if (viewer.value) {
      viewer.value.destroy()
      viewer.value = null
    }
    isReady.value = false
  }

  onUnmounted(() => {
    destroy()
  })

  return {
    viewer,
    isReady,
    zoom,
    center,
    cursorPosition,
    initViewer,
    zoomTo,
    zoomToLevel,
    resetView,
    screenToImageCoordinates,
    imageToScreenCoordinates,
    addOverlay,
    updateOverlay,
    removeOverlay,
    forceRedraw,
    destroy
  }
}
