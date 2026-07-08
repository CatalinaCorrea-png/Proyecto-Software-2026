import { useEffect, useRef } from 'react'
import './WebGLStars.css'

// Fondo de estrellas en WebGL (shader GLSL a pantalla completa), inspirado en el
// "animated hero with WebGL glitter" de 21st, pero en formato ESTRELLAS que
// titilan/brillan en vez de glitter. Sin dependencias (WebGL puro): un solo quad
// a pantalla completa, la GPU hace todo → barato y fluido.

const VERT = `
attribute vec2 aPos;
void main() { gl_Position = vec4(aPos, 0.0, 1.0); }
`

const FRAG = `
precision highp float;

uniform vec2 uRes;
uniform float uTime;
uniform float uSpeed;
uniform float uIntensity;

float hash21(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

// Una capa de estrellas: rejilla de celdas; algunas contienen una estrella con
// núcleo brillante, parpadeo (twinkle) y, en las más brillantes, destellos en
// cruz (efecto "estrella que brilla").
vec3 starLayer(vec2 uv, float t) {
  vec3 acc = vec3(0.0);
  vec2 gv = fract(uv) - 0.5;
  vec2 id = floor(uv);

  for (int y = -1; y <= 1; y++) {
    for (int x = -1; x <= 1; x++) {
      vec2 o = vec2(float(x), float(y));
      float n = hash21(id + o + 1.0);
      float present = step(0.60, n);            // ~40% de celdas tienen estrella
      float n2 = fract(n * 34.56);
      vec2 pos = o + (vec2(n, n2) - 0.5) * 0.85; // posición dentro de la celda
      vec2 rel = gv - pos;
      float dist = length(rel);

      float size = mix(0.010, 0.05, fract(n * 91.7));
      float core = smoothstep(size, 0.0, dist);

      // Parpadeo: cada estrella con su fase/velocidad.
      float tw = 0.45 + 0.55 * sin(t * (1.1 + n * 2.4) + n * 6.2831);

      // Destellos en cruz para las estrellas más brillantes.
      float bright = fract(n * 57.31);
      float sb = smoothstep(0.72, 1.0, bright);
      float sx = smoothstep(size * 7.0, 0.0, abs(rel.x)) * smoothstep(size * 0.5, 0.0, abs(rel.y));
      float sy = smoothstep(size * 7.0, 0.0, abs(rel.y)) * smoothstep(size * 0.5, 0.0, abs(rel.x));
      float spikes = (sx + sy) * sb;

      // Color: mayoría blanco-azulado frío; unas pocas ámbar (paleta SAR).
      float warm = step(0.90, fract(n * 12.34));
      vec3 tint = mix(vec3(0.82, 0.9, 1.0), vec3(1.0, 0.52, 0.12), warm);

      acc += tint * present * (core + spikes * 0.55) * tw;
    }
  }
  return acc;
}

void main() {
  vec2 frag = gl_FragCoord.xy;
  vec2 uv = (frag - 0.5 * uRes) / uRes.y;
  float t = uTime * uSpeed;

  // Fondo: navy muy oscuro de la app (#080b14), con un leve degradé vertical.
  float vy = frag.y / uRes.y;
  vec3 col = mix(vec3(0.028, 0.037, 0.066), vec3(0.020, 0.027, 0.048), vy);

  // Nebulosa tenue para dar profundidad (azul frío + apenas ámbar), muy sutil.
  float neb = smoothstep(0.9, 0.0, length(uv - vec2(0.5, -0.1)));
  col += vec3(0.03, 0.05, 0.09) * neb * 0.5;

  // Tres capas de estrellas a distinta escala/deriva (parallax + densidad).
  vec3 stars = vec3(0.0);
  stars += starLayer(uv * 8.0  + vec2(t * 0.012, 0.0), t) * 0.95;
  stars += starLayer(uv * 14.0 + vec2(t * 0.024, 5.0), t * 1.15 + 3.0) * 0.6;
  stars += starLayer(uv * 22.0 + vec2(t * 0.04, 9.0), t * 1.3 + 7.0) * 0.38;

  col += stars * (uIntensity * 0.12);

  gl_FragColor = vec4(col, 1.0);
}
`

function compile(gl: WebGLRenderingContext, type: number, src: string) {
  const sh = gl.createShader(type)!
  gl.shaderSource(sh, src)
  gl.compileShader(sh)
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(sh)
    console.error('[WebGLStars] compile fail', type === gl.VERTEX_SHADER ? 'VERT' : 'FRAG', log)
    throw new Error(log || 'shader compile error')
  }
  return sh
}

type WebGLStarsProps = {
  /** Velocidad del titileo/deriva (como el `speed` del componente original). */
  speed?: number
  /** Brillo/densidad aparente de las estrellas (como el `intensity`). */
  intensity?: number
  className?: string
}

export function WebGLStars({ speed = 0.6, intensity = 4.5, className }: WebGLStarsProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl', {
      alpha: false,
      antialias: false,
      powerPreference: 'high-performance',
      preserveDrawingBuffer: false,
    })
    if (!gl) {
      // Sin WebGL: el CSS deja un fondo sólido de respaldo.
      return
    }

    let program: WebGLProgram | null = null
    try {
      program = gl.createProgram()!
      gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, VERT))
      gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, FRAG))
      gl.linkProgram(program)
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        throw new Error(gl.getProgramInfoLog(program) || 'link error')
      }
    } catch (e) {
      console.warn('[WebGLStars] no se pudo inicializar el shader:', e)
      return
    }
    gl.useProgram(program)

    // Triángulo a pantalla completa.
    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW)
    const aPos = gl.getAttribLocation(program, 'aPos')
    gl.enableVertexAttribArray(aPos)
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

    const uRes = gl.getUniformLocation(program, 'uRes')
    const uTime = gl.getUniformLocation(program, 'uTime')
    const uSpeed = gl.getUniformLocation(program, 'uSpeed')
    const uIntensity = gl.getUniformLocation(program, 'uIntensity')

    const isMobile = window.matchMedia('(max-width: 768px)').matches
    const reducedMQ = window.matchMedia('(prefers-reduced-motion: reduce)')
    const dprCap = isMobile ? 1.5 : 2

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, dprCap)
      const w = Math.floor(canvas.clientWidth * dpr)
      const h = Math.floor(canvas.clientHeight * dpr)
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w
        canvas.height = h
      }
      gl.viewport(0, 0, canvas.width, canvas.height)
      gl.uniform2f(uRes, canvas.width, canvas.height)
    }

    gl.uniform1f(uSpeed, speed)
    gl.uniform1f(uIntensity, intensity)
    resize()
    window.addEventListener('resize', resize)

    let raf = 0
    const start = performance.now()

    const renderFrame = (timeSec: number) => {
      gl.uniform1f(uTime, timeSec)
      gl.drawArrays(gl.TRIANGLES, 0, 3)
    }

    const loop = () => {
      renderFrame((performance.now() - start) / 1000)
      raf = requestAnimationFrame(loop)
    }

    // prefers-reduced-motion: campo estático (un frame, sin titileo) para no
    // animar. Si cambia la preferencia, arrancamos/paramos el loop.
    const applyMotion = () => {
      cancelAnimationFrame(raf)
      if (reducedMQ.matches) {
        renderFrame(0)
      } else {
        loop()
      }
    }
    applyMotion()
    reducedMQ.addEventListener('change', applyMotion)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      reducedMQ.removeEventListener('change', applyMotion)
      // No usamos WEBGL_lose_context: getContext() del mismo canvas devuelve
      // SIEMPRE el mismo contexto, así que perderlo rompería el remonte (p. ej.
      // el doble montaje de React StrictMode en dev). Basta con liberar recursos.
      gl.deleteProgram(program)
      gl.deleteBuffer(buf)
    }
  }, [speed, intensity])

  return (
    <div className={`webgl-stars${className ? ` ${className}` : ''}`} aria-hidden="true">
      <canvas ref={canvasRef} className="webgl-stars__canvas" />
    </div>
  )
}

export default WebGLStars
