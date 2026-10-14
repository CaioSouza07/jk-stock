import { useCallback, useEffect, useRef, useState } from 'react'

import { createBarcodeDetector } from '../lib/barcodeDetector'
import { extractAccessKey } from '../utils/accessKey'

const SCAN_INTERVAL_MS = 120
const ZOOM_LEVEL = 2

// High resolution matters: the DANFE barcode is long and dense (44 digits)
const CAMERA_CONSTRAINTS = {
  audio: false,
  video: {
    facingMode: { ideal: 'environment' },
    width: { ideal: 1920 },
    height: { ideal: 1080 },
  },
}

class ScannerError extends Error {}

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

function readCapabilities(track) {
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

    const start = async () => {
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
        throw new ScannerError(
          'A câmera só funciona em HTTPS ou localhost. Use a digitação manual abaixo.',
        )
      }
      const detectorPromise = createBarcodeDetector().catch(() => {
        throw new ScannerError('Não foi possível carregar o leitor de código de barras.')
      })
      const [detector, mediaStream] = await Promise.all([
        detectorPromise,
        navigator.mediaDevices.getUserMedia(CAMERA_CONSTRAINTS),
      ])
      stream = mediaStream
      if (cancelled) {
        stopStream(stream)
        return
      }

      const [track] = stream.getVideoTracks()
      trackRef.current = track
      const caps = readCapabilities(track)
      if (caps.continuousFocus) {
        track.applyConstraints({ advanced: [{ focusMode: 'continuous' }] }).catch(() => {})
      }
      setCapabilities(caps)

      const video = videoRef.current
      video.srcObject = stream
      await video.play()
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
