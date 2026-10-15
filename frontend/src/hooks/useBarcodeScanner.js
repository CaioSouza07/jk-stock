import { useCallback, useEffect, useRef, useState } from 'react'

import { createBarcodeDetector } from '../lib/barcodeDetector'
import { extractAccessKey } from '../utils/accessKey'

const SCAN_INTERVAL_MS = 120
const ZOOM_LEVEL = 2
const PHOTO_CAPABILITIES_WAIT_MS = 1000

// Rear camera that has the torch, remembered so the lens search runs only once per device
const CAMERA_STORAGE_KEY = 'jkstock.cameraId'
// Saved when no rear lens exposes a torch: keep the browser's default camera
const DEFAULT_CAMERA = 'default'
const BACK_CAMERA_LABEL = /back|rear|traseira|environment/i

class ScannerError extends Error {}
class CancelledError extends Error {}

// High resolution matters: the DANFE barcode is long and dense (44 digits)
function cameraConstraints(deviceId) {
  const video = { width: { ideal: 1920 }, height: { ideal: 1080 } }
  return {
    audio: false,
    video: deviceId
      ? { ...video, deviceId: { exact: deviceId } }
      : { ...video, facingMode: { ideal: 'environment' } },
  }
}

function readSavedCamera() {
  try {
    return localStorage.getItem(CAMERA_STORAGE_KEY)
  } catch {
    return null
  }
}

function saveCamera(deviceId) {
  try {
    localStorage.setItem(CAMERA_STORAGE_KEY, deviceId)
  } catch {
    // Private mode: the search simply runs again next time
  }
}

function errorMessage(error) {
  if (error instanceof ScannerError) return error.message
  switch (error?.name) {
    case 'NotAllowedError':
      return 'Permissão da câmera negada. Libere o acesso à câmera nas configurações do navegador.'
    case 'NotFoundError':
    case 'OverconstrainedError':
      return 'Nenhuma câmera encontrada neste aparelho.'
    case 'NotReadableError':
      return 'A câmera está sendo usada por outro aplicativo.'
    default:
      return 'Não foi possível iniciar o leitor. Use a digitação manual abaixo.'
  }
}

function stopStream(stream) {
  stream?.getTracks().forEach((track) => track.stop())
}

async function readCapabilities(track) {
  // Some Android devices only report the torch after the photo capabilities are queried
  if ('ImageCapture' in window) {
    const photo = new window.ImageCapture(track).getPhotoCapabilities().catch(() => null)
    const timeout = new Promise((resolve) => setTimeout(resolve, PHOTO_CAPABILITIES_WAIT_MS))
    await Promise.race([photo, timeout])
  }
  const caps = track.getCapabilities?.() ?? {}
  return {
    torch: caps.torch === true,
    zoom: caps.zoom && caps.zoom.max >= ZOOM_LEVEL ? caps.zoom : null,
    continuousFocus: caps.focusMode?.includes('continuous') ?? false,
  }
}

/**
 * Opens the rear camera into videoRef and calls onDetect(accessKey) once a frame
 * contains a 44-digit key. Other barcodes in view are ignored.
 */
export function useBarcodeScanner({ videoRef, onDetect }) {
  const [error, setError] = useState(null)
  const [ready, setReady] = useState(false)
  const [capabilities, setCapabilities] = useState({ torch: false, zoom: null })
  const [torchOn, setTorchOn] = useState(false)
  const [zoomOn, setZoomOn] = useState(false)
  const trackRef = useRef(null)
  const onDetectRef = useRef(onDetect)

  useEffect(() => {
    onDetectRef.current = onDetect
  }, [onDetect])

  useEffect(() => {
    let cancelled = false
    let stream = null
    let timer = null

    const scan = async (detector, video) => {
      if (cancelled) return
      try {
        if (video.readyState >= video.HAVE_CURRENT_DATA) {
          const barcodes = await detector.detect(video)
          const key = barcodes.map((barcode) => extractAccessKey(barcode.rawValue)).find(Boolean)
          if (key && !cancelled) {
            cancelled = true
            navigator.vibrate?.(100)
            onDetectRef.current(key)
            return
          }
        }
      } catch {
        // A single bad frame must not stop the loop
      }
      timer = setTimeout(() => scan(detector, video), SCAN_INTERVAL_MS)
    }

    const openCamera = async (deviceId) => {
      const mediaStream = await navigator.mediaDevices.getUserMedia(cameraConstraints(deviceId))
      if (cancelled) {
        stopStream(mediaStream)
        throw new CancelledError()
      }
      stream = mediaStream
      return mediaStream.getVideoTracks()[0]
    }

    const openPreferredCamera = async (savedId) => {
      if (savedId && savedId !== DEFAULT_CAMERA) {
        try {
          return await openCamera(savedId)
        } catch (openError) {
          if (openError instanceof CancelledError) throw openError
          // Saved camera no longer available: fall back to the default one
        }
      }
      return openCamera(null)
    }

    // Phones with several rear lenses may open one without the flash LED.
    // Returns the track to use: a lens with torch, or the original one.
    const findTorchCamera = async (currentTrack) => {
      const currentId = currentTrack.getSettings().deviceId
      const devices = await navigator.mediaDevices.enumerateDevices()
      const candidates = devices.filter(
        (device) =>
          device.kind === 'videoinput' &&
          device.deviceId &&
          device.deviceId !== currentId &&
          BACK_CAMERA_LABEL.test(device.label),
      )
      if (candidates.length === 0) return { track: currentTrack, torchId: null }

      for (const device of candidates) {
        // Many phones cannot keep two cameras open at once
        stopStream(stream)
        try {
          const track = await openCamera(device.deviceId)
          if ((await readCapabilities(track)).torch) return { track, torchId: device.deviceId }
        } catch (openError) {
          if (openError instanceof CancelledError) throw openError
        }
      }
      stopStream(stream)
      return { track: await openPreferredCamera(currentId), torchId: null }
    }

    const start = async () => {
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
        throw new ScannerError(
          'A câmera só funciona em HTTPS ou localhost. Use a digitação manual abaixo.',
        )
      }
      const detectorPromise = createBarcodeDetector().catch(() => {
        throw new ScannerError('Não foi possível carregar o leitor de código de barras.')
      })
      const savedId = readSavedCamera()
      const [detector, firstTrack] = await Promise.all([
        detectorPromise,
        openPreferredCamera(savedId),
      ])
      let track = firstTrack

      if (savedId === null && !(await readCapabilities(track)).torch) {
        const found = await findTorchCamera(track)
        track = found.track
        saveCamera(found.torchId ?? DEFAULT_CAMERA)
      }
      if (cancelled) return

      const video = videoRef.current
      video.srcObject = stream
      await video.play()
      // Read again with the video running: some devices only report the torch now
      const caps = await readCapabilities(track)
      if (cancelled) return

      trackRef.current = track
      if (caps.continuousFocus) {
        track.applyConstraints({ advanced: [{ focusMode: 'continuous' }] }).catch(() => {})
      }
      setCapabilities(caps)
      setReady(true)
      scan(detector, video)
    }

    start().catch((startError) => {
      stopStream(stream)
      if (!cancelled) setError(errorMessage(startError))
    })

    return () => {
      cancelled = true
      clearTimeout(timer)
      stopStream(stream)
      trackRef.current = null
    }
  }, [videoRef])

  const toggleTorch = useCallback(() => {
    const next = !torchOn
    trackRef.current
      ?.applyConstraints({ advanced: [{ torch: next }] })
      .then(() => setTorchOn(next))
      .catch(() => {})
  }, [torchOn])

  const toggleZoom = useCallback(() => {
    if (!capabilities.zoom) return
    const next = !zoomOn
    const zoom = next ? ZOOM_LEVEL : capabilities.zoom.min
    trackRef.current
      ?.applyConstraints({ advanced: [{ zoom }] })
      .then(() => setZoomOn(next))
      .catch(() => {})
  }, [capabilities.zoom, zoomOn])

  return {
    error,
    ready,
    torch: { supported: capabilities.torch, on: torchOn, toggle: toggleTorch },
    zoom: { supported: Boolean(capabilities.zoom), on: zoomOn, toggle: toggleZoom },
  }
}
