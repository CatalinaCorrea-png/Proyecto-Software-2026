import { useEffect, useRef, useState } from 'react'
import createGlobe from 'cobe'
import './GlobeHero.css'

// ── Marcadores SAR (lat, lng) con retardo para escalonar el "pulso" ──────────
// Puntos de interés (centros de operaciones ficticios). Se dibujan como overlay
// SVG proyectado sobre la esfera para poder animar los anillos concéntricos,
// algo que cobe no permite sobre sus marcadores nativos (se hornean al crear).
type Marker = { lat: number; lng: number; delay: number }
const MARKERS: Marker[] = [
  { lat: -34.61, lng: -58.38, delay: 0 },    // Buenos Aires
  { lat: 40.71, lng: -74.01, delay: 0.6 },   // Nueva York
  { lat: 51.51, lng: -0.13, delay: 1.2 },    // Londres
  { lat: 35.68, lng: 139.69, delay: 0.9 },   // Tokio
  { lat: -33.87, lng: 151.21, delay: 1.5 },  // Sídney
  { lat: 19.43, lng: -99.13, delay: 0.3 },   // Ciudad de México
  { lat: 28.61, lng: 77.21, delay: 1.8 },    // Nueva Delhi
]

const DEG = Math.PI / 180
// Radio del marcador = radio de la esfera visible de cobe (ee = 0.8), para que
// los puntos queden SOBRE la superficie del globo. Con el valor elevado (0.85)
// los marcadores cercanos al borde/polo se proyectaban por fuera de la silueta
// del globo (se "notaban por arriba"). En 0.8 quedan clavados en la superficie.
const MARKER_R = 0.8

// Proyección idéntica a la de cobe (funciones U + O de su fuente): convierte
// (lat, lng) + rotación actual (phi/theta) a coords de pantalla, de modo que los
// pulsos queden clavados exactamente sobre la superficie del mapa. `s` = lado del
// escenario cuadrado en px (canvas cuadrado, offset 0, scale 1).
function project(lat: number, lng: number, phi: number, theta: number, s: number) {
  const latR = lat * DEG
  const lngR = lng * DEG - Math.PI
  // U(location) escalado por el radio del marcador.
  const t0 = MARKER_R * -Math.cos(latR) * Math.cos(lngR)
  const t1 = MARKER_R * Math.sin(latR)
  const t2 = MARKER_R * Math.cos(latR) * Math.sin(lngR)
  // O(): rotación por phi (vertical) y theta (inclinación) + proyección ortográfica.
  const cosP = Math.cos(phi), sinP = Math.sin(phi)
  const cosT = Math.cos(theta), sinT = Math.sin(theta)
  const cx = cosP * t0 + sinP * t2
  const cy = sinP * sinT * t0 + cosT * t1 - cosP * sinT * t2
  const depth = -sinP * cosT * t0 + sinT * t1 + cosP * cosT * t2
  return {
    sx: ((cx + 1) / 2) * s,
    sy: ((-cy + 1) / 2) * s,
    // Ocultamos un poco antes del horizonte exacto (no en depth 0) para que ni
    // el punto ni sus anillos de pulso asomen por el borde con ángulo rasante.
    front: depth >= 0.06,
  }
}

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia(query).matches : false,
  )
  useEffect(() => {
    const mql = window.matchMedia(query)
    const onChange = () => setMatches(mql.matches)
    onChange()
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [query])
  return matches
}

type GlobeHeroProps = { className?: string }

/**
 * Globo WebGL oscuro (cobe) con anillos de pulso sobre marcadores.
 *  - Idle: autorrotación suave.
 *  - Interacción: arrastrar para girar, con inercia (damping).
 *  - Respeta prefers-reduced-motion (estático, sin pulso ni arrastre) y baja
 *    la resolución en mobile.
 */
export function GlobeHero({ className }: GlobeHeroProps) {
  const reducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)')
  const isMobile = useMediaQuery('(max-width: 768px)')

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const stageRef = useRef<HTMLDivElement>(null)
  // Un <g> por marcador; posicionamos por frame sin re-render de React.
  const markerRefs = useRef<(SVGGElement | null)[]>([])

  useEffect(() => {
    const canvas = canvasRef.current
    const stage = stageRef.current
    if (!canvas || !stage) return

    const dpr = Math.min(window.devicePixelRatio || 1, isMobile ? 1.5 : 2)

    // Estado de rotación / arrastre (en refs para no re-renderizar por frame).
    let phi = 0
    let theta = 0.25
    let velocity = 0 // inercia del arrastre
    let dragging = false
    let lastX = 0
    let lastY = 0
    let size = stage.offsetWidth

    const AUTO_SPEED = reducedMotion ? 0 : 0.0035
    const FRICTION = 0.94

    const onResize = () => {
      size = stage.offsetWidth
    }
    window.addEventListener('resize', onResize)
    onResize()

    // ── Arrastre para girar (deshabilitado si reduced-motion) ──
    const onPointerDown = (e: PointerEvent) => {
      if (reducedMotion) return
      dragging = true
      velocity = 0
      lastX = e.clientX
      lastY = e.clientY
      canvas.style.cursor = 'grabbing'
      canvas.setPointerCapture(e.pointerId)
    }
    const onPointerMove = (e: PointerEvent) => {
      if (!dragging) return
      const dx = e.clientX - lastX
      const dy = e.clientY - lastY
      lastX = e.clientX
      lastY = e.clientY
      phi += dx * 0.005
      velocity = dx * 0.005 // se conserva al soltar (inercia)
      theta = Math.max(-0.6, Math.min(0.6, theta + dy * 0.005))
    }
    const onPointerUp = (e: PointerEvent) => {
      dragging = false
      canvas.style.cursor = 'grab'
      try { canvas.releasePointerCapture(e.pointerId) } catch { /* noop */ }
    }
    if (!reducedMotion) {
      canvas.addEventListener('pointerdown', onPointerDown)
      canvas.addEventListener('pointermove', onPointerMove)
      canvas.addEventListener('pointerup', onPointerUp)
      canvas.addEventListener('pointerleave', onPointerUp)
      canvas.style.cursor = 'grab'
    }

    const globe = createGlobe(canvas, {
      devicePixelRatio: dpr,
      width: size * dpr,
      height: size * dpr,
      phi: 0,
      theta,
      dark: 1,
      diffuse: 1.25,
      mapSamples: 16000,
      mapBrightness: 5,
      // Paleta "centro de comando": base azul-pizarra oscura, halo frío.
      baseColor: [0.16, 0.2, 0.26],
      markerColor: [1, 0.43, 0],
      glowColor: [0.14, 0.22, 0.34],
      markers: [], // los marcadores/pulsos se dibujan como overlay SVG
    })

    // En cobe v2 el bucle de animación es externo: cada frame calculamos la
    // rotación (autorrotación + inercia del arrastre) y llamamos update().
    let raf = 0
    let shown = false
    const render = () => {
      if (!dragging) {
        phi += AUTO_SPEED + velocity
        velocity *= FRICTION
      }
      globe.update({ phi, theta, width: size * dpr, height: size * dpr })

      // Reproyectar los marcadores sobre la esfera y ubicar los pulsos.
      for (let i = 0; i < MARKERS.length; i++) {
        const g = markerRefs.current[i]
        if (!g) continue
        const m = MARKERS[i]
        const { sx, sy, front } = project(m.lat, m.lng, phi, theta, size)
        g.setAttribute('transform', `translate(${sx} ${sy})`)
        // Ocultar suavemente los que están en la cara oculta del globo.
        g.style.opacity = front ? '1' : '0'
      }

      if (!shown) {
        shown = true
        canvas.style.opacity = '1' // fade-in cuando ya hay un frame dibujado
      }
      raf = requestAnimationFrame(render)
    }
    raf = requestAnimationFrame(render)

    return () => {
      cancelAnimationFrame(raf)
      globe.destroy()
      window.removeEventListener('resize', onResize)
      canvas.removeEventListener('pointerdown', onPointerDown)
      canvas.removeEventListener('pointermove', onPointerMove)
      canvas.removeEventListener('pointerup', onPointerUp)
      canvas.removeEventListener('pointerleave', onPointerUp)
    }
  }, [reducedMotion, isMobile])

  return (
    <div className={`globe-hero${className ? ` ${className}` : ''}`}>
      <div className="globe-hero__glow" aria-hidden="true" />
      <div ref={stageRef} className="globe-hero__stage">
        <canvas
          ref={canvasRef}
          className="globe-hero__canvas"
          aria-label="Globo terráqueo con centros de operación SAR"
        />
        {/* Overlay de pulsos: los anillos crecen y se desvanecen (CSS); la
            posición la fija el bucle de render por frame. */}
        <svg className="globe-hero__markers" aria-hidden="true">
          {MARKERS.map((m, i) => (
            <g
              key={i}
              ref={(el) => { markerRefs.current[i] = el }}
              style={{ '--pulse-delay': `${m.delay}s` } as React.CSSProperties}
            >
              {!reducedMotion && (
                <>
                  <circle className="globe-hero__ring" r="6" />
                  <circle className="globe-hero__ring globe-hero__ring--2" r="6" />
                </>
              )}
              <circle className="globe-hero__dot" r="2.6" />
            </g>
          ))}
        </svg>
      </div>
    </div>
  )
}

export default GlobeHero
