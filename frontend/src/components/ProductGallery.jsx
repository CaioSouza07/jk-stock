import { useRef, useState } from 'react'

import { cn } from '../utils/cn'
import { ImagePlaceholder, ProductImage } from './ProductImage'

function ArrowButton({ direction, onClick }) {
  const previous = direction === 'previous'
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={previous ? 'Foto anterior' : 'Próxima foto'}
      className={cn(
        'absolute top-1/2 flex size-10 -translate-y-1/2 items-center justify-center rounded-full bg-ink/60 text-white shadow backdrop-blur transition-colors hover:bg-ink/80',
        previous ? 'left-2' : 'right-2',
      )}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="size-5" aria-hidden="true">
        <path d={previous ? 'm15 18-6-6 6-6' : 'm9 18 6-6-6-6'} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>
  )
}

/** Product photos: swipe or use the arrows. Native scroll-snap does the sliding. */
export function ProductGallery({ images, alt }) {
  const scrollerRef = useRef(null)
  const [index, setIndex] = useState(0)

  if (images.length === 0) {
    return (
      <div className="flex h-28 flex-col items-center justify-center gap-1 bg-background text-secondary">
        <ImagePlaceholder />
        <span className="text-xs font-semibold">Sem foto</span>
      </div>
    )
  }

  const goTo = (target) => {
    const scroller = scrollerRef.current
    scroller.scrollTo({ left: target * scroller.clientWidth, behavior: 'smooth' })
  }

  const handleScroll = (event) => {
    const scroller = event.currentTarget
    setIndex(Math.round(scroller.scrollLeft / scroller.clientWidth))
  }

  return (
    <div className="relative aspect-[4/3] w-full bg-white" aria-roledescription="carrossel">
      <div
        ref={scrollerRef}
        onScroll={handleScroll}
        className="flex size-full snap-x snap-mandatory overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {images.map((src, i) => (
          <ProductImage
            key={`${i}-${src}`}
            src={src}
            alt={images.length > 1 ? `${alt} (foto ${i + 1} de ${images.length})` : alt}
            className="size-full shrink-0 snap-center"
          />
        ))}
      </div>

      {images.length > 1 && (
        <>
          {index > 0 && <ArrowButton direction="previous" onClick={() => goTo(index - 1)} />}
          {index < images.length - 1 && (
            <ArrowButton direction="next" onClick={() => goTo(index + 1)} />
          )}
          <span className="pointer-events-none absolute bottom-2 right-2 rounded-full bg-ink/60 px-2.5 py-0.5 text-xs font-semibold text-white">
            {index + 1}/{images.length}
          </span>
        </>
      )}
    </div>
  )
}
