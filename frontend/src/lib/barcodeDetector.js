// Self-hosted: the ponyfill would otherwise download the .wasm from a CDN
import zxingWasmUrl from 'zxing-wasm/reader/zxing_reader.wasm?url'

// DANFE barcode is Code 128; NFC-e has a QR code with the key in the URL
const FORMATS = ['code_128', 'qr_code']

async function createNativeDetector() {
  if (!('BarcodeDetector' in window)) return null
  try {
    const supported = await window.BarcodeDetector.getSupportedFormats()
    if (!FORMATS.every((format) => supported.includes(format))) return null
    return new window.BarcodeDetector({ formats: FORMATS })
  } catch {
    return null
  }
}

async function createWasmDetector() {
  const { BarcodeDetector, prepareZXingModule } = await import('barcode-detector/ponyfill')
  await prepareZXingModule({
    overrides: {
      locateFile: (path, prefix) => (path.endsWith('.wasm') ? zxingWasmUrl : prefix + path),
    },
    fireImmediately: true,
  })
  return new BarcodeDetector({ formats: FORMATS })
}

/**
 * Native BarcodeDetector when available (Chrome on Android uses the same engine as the
 * system camera); otherwise ZXing compiled to WebAssembly (iPhone, desktop Firefox...).
 */
export async function createBarcodeDetector() {
  return (await createNativeDetector()) ?? (await createWasmDetector())
}
