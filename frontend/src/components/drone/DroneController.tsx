import { useCallback, useEffect, useRef, useState } from 'react'

const API = 'http://localhost:8000'
const SEND_INTERVAL_MS = 100

interface JoystickProps {
  onChange: (roll: number, pitch: number) => void
  armed: boolean
}

function Joystick({ onChange, armed }: JoystickProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [knob, setKnob] = useState({ x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)

  const SIZE = 134
  const KNOB_R = 18
  const MAX_R = SIZE / 2 - KNOB_R - 4

  const computePos = (e: React.PointerEvent) => {
    const rect = containerRef.current!.getBoundingClientRect()
    let dx = e.clientX - (rect.left + rect.width / 2)
    let dy = e.clientY - (rect.top + rect.height / 2)
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist > MAX_R) {
      dx = (dx / dist) * MAX_R
      dy = (dy / dist) * MAX_R
    }
    return { x: dx, y: dy }
  }

  const emit = (x: number, y: number) => {
    onChange(
      Math.round((x / MAX_R) * 100),
      Math.round((-y / MAX_R) * 100)  // eje Y invertido: arriba = pitch positivo
    )
  }

  const handleDown = (e: React.PointerEvent) => {
    if (!armed) return
    containerRef.current?.setPointerCapture(e.pointerId)
    setDragging(true)
    const pos = computePos(e)
    setKnob(pos)
    emit(pos.x, pos.y)
  }

  const handleMove = (e: React.PointerEvent) => {
    if (!dragging) return
    const pos = computePos(e)
    setKnob(pos)
    emit(pos.x, pos.y)
  }

  const handleUp = useCallback(() => {
    setDragging(false)
    setKnob({ x: 0, y: 0 })
    onChange(0, 0)
  }, [onChange])

  // Si se desarma externamente, centrar el knob
  useEffect(() => {
    if (!armed) handleUp()
  }, [armed, handleUp])

  const active = armed && dragging

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <span style={{ color: '#546E7A', fontSize: 9, fontFamily: 'monospace', letterSpacing: 1 }}>
        PITCH / ROLL
      </span>
      <div
        ref={containerRef}
        onPointerDown={handleDown}
        onPointerMove={handleMove}
        onPointerUp={handleUp}
        onPointerCancel={handleUp}
        style={{
          width: SIZE,
          height: SIZE,
          borderRadius: '50%',
          background: '#060D14',
          border: `1px solid ${armed ? '#1E5F8F' : '#1A2A3A'}`,
          position: 'relative',
          cursor: armed ? 'crosshair' : 'not-allowed',
          touchAction: 'none',
          userSelect: 'none',
          transition: 'border-color 0.2s',
        }}
      >
        {/* crosshair horizontal */}
        <div style={{
          position: 'absolute', top: '50%', left: '12%', right: '12%',
          height: 1, background: '#1E3A5F', transform: 'translateY(-50%)',
          pointerEvents: 'none',
        }} />
        {/* crosshair vertical */}
        <div style={{
          position: 'absolute', left: '50%', top: '12%', bottom: '12%',
          width: 1, background: '#1E3A5F', transform: 'translateX(-50%)',
          pointerEvents: 'none',
        }} />
        {/* knob */}
        <div style={{
          position: 'absolute',
          width: KNOB_R * 2,
          height: KNOB_R * 2,
          borderRadius: '50%',
          background: active ? '#00BCD4' : armed ? '#0A2A3A' : '#111E2A',
          border: `2px solid ${armed ? '#00BCD466' : '#1E3A5F'}`,
          left: `calc(50% + ${knob.x}px - ${KNOB_R}px)`,
          top: `calc(50% + ${knob.y}px - ${KNOB_R}px)`,
          transition: dragging ? 'none' : 'left 0.15s ease-out, top 0.15s ease-out, background 0.15s',
          pointerEvents: 'none',
          boxShadow: active ? '0 0 8px #00BCD480' : 'none',
        }} />
      </div>
    </div>
  )
}

export function DroneController() {
  const [throttle, setThrottle] = useState(0)
  const [pitch, setPitch] = useState(0)
  const [roll, setRoll] = useState(0)
  const [armed, setArmed] = useState(false)

  const cmdRef = useRef({ throttle: 0, yaw: 0, pitch: 0, roll: 0 })

  useEffect(() => {
    cmdRef.current = { throttle, yaw: 0, pitch, roll }
  }, [throttle, pitch, roll])

  const handleJoystick = useCallback((r: number, p: number) => {
    setRoll(r)
    setPitch(p)
  }, [])

  // Loop de envío a 10 Hz cuando está armado
  useEffect(() => {
    if (!armed) return
    const id = setInterval(() => {
      fetch(`${API}/drone/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cmdRef.current),
      }).catch(() => {})
    }, SEND_INTERVAL_MS)
    return () => clearInterval(id)
  }, [armed])

  const toggleArm = () => {
    if (armed) {
      setThrottle(0)
      setRoll(0)
      setPitch(0)
      fetch(`${API}/drone/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ throttle: 0, yaw: 0, pitch: 0, roll: 0 }),
      }).catch(() => {})
    }
    setArmed(a => !a)
  }

  const throttlePct = Math.round((throttle / 255) * 100)

  return (
    <div style={{
      background: '#0D1B2A',
      border: '1px solid #1E3A5F',
      borderRadius: 8,
      padding: '10px 12px',
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
    }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#78909C', fontSize: 11, fontFamily: 'monospace', letterSpacing: 1 }}>
          CONTROL DE VUELO
        </span>
        <button
          onClick={toggleArm}
          style={{
            padding: '3px 12px',
            fontSize: 10,
            fontFamily: 'monospace',
            fontWeight: 'bold',
            letterSpacing: 1,
            border: `1px solid ${armed ? '#FF5252' : '#37474F'}`,
            borderRadius: 4,
            cursor: 'pointer',
            background: armed ? '#FF525220' : 'transparent',
            color: armed ? '#FF5252' : '#546E7A',
            transition: 'all 0.2s',
          }}
        >
          {armed ? '■ DISARM' : '▶ ARM'}
        </button>
      </div>

      {/* Controles */}
      <div style={{ display: 'flex', gap: 14, alignItems: 'center', justifyContent: 'center' }}>

        {/* Throttle */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <span style={{ color: '#546E7A', fontSize: 9, fontFamily: 'monospace', letterSpacing: 1 }}>
            THROTTLE
          </span>
          <span style={{
            color: throttle > 0 ? '#FF6D00' : '#37474F',
            fontSize: 10, fontFamily: 'monospace', fontWeight: 'bold',
            transition: 'color 0.2s'
          }}>
            {throttlePct}%
          </span>

          {/* Barra visual de fondo + relleno */}
          <div style={{ position: 'relative', height: 134, width: 36 }}>
            {/* Track de fondo */}
            <div style={{
              position: 'absolute', left: '50%', top: 0, bottom: 0,
              width: 6, transform: 'translateX(-50%)',
              background: '#060D14', border: '1px solid #1A2A3A', borderRadius: 3,
            }} />
            {/* Relleno dinámico (de abajo hacia arriba) */}
            <div style={{
              position: 'absolute', left: '50%', bottom: 0,
              width: 6, height: `${throttlePct}%`,
              transform: 'translateX(-50%)',
              background: armed ? '#FF6D00' : '#1A2A3A',
              borderRadius: 3,
              transition: 'height 0.05s, background 0.2s',
            }} />
            {/* Slider rotado */}
            <input
              type="range"
              min={0} max={255}
              value={throttle}
              disabled={!armed}
              onChange={e => setThrottle(Number(e.target.value))}
              style={{
                position: 'absolute',
                width: 134,
                height: 36,
                top: '50%',
                left: '50%',
                margin: 0,
                padding: 0,
                transform: 'translate(-50%, -50%) rotate(-90deg)',
                opacity: 0,          // invisible pero funcional
                cursor: armed ? 'pointer' : 'not-allowed',
                zIndex: 2,
              }}
            />
          </div>

          <span style={{ color: '#37474F', fontSize: 9, fontFamily: 'monospace' }}>0%</span>
        </div>

        {/* Joystick */}
        <Joystick onChange={handleJoystick} armed={armed} />
      </div>

      {/* Valores en tiempo real */}
      <div style={{
        display: 'flex', justifyContent: 'space-around',
        fontFamily: 'monospace', fontSize: 9, color: '#37474F',
        borderTop: '1px solid #0F1E2E', paddingTop: 6,
      }}>
        <span style={{ color: throttle > 0 ? '#FF6D0099' : '#37474F' }}>T:{throttle}</span>
        <span style={{ color: pitch !== 0 ? '#00BCD499' : '#37474F' }}>P:{pitch > 0 ? '+' : ''}{pitch}</span>
        <span style={{ color: roll !== 0 ? '#00BCD499' : '#37474F' }}>R:{roll > 0 ? '+' : ''}{roll}</span>
        <span style={{ color: '#37474F' }}>Y:0</span>
      </div>

    </div>
  )
}
