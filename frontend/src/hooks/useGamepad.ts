import { useEffect, useRef, useState } from 'react'

export interface GamepadAxes {
  throttle: number  // 0-255
  yaw:      number  // -100..100
  pitch:    number  // -100..100
  roll:     number  // -100..100
}

const DEADZONE = 0.15

function dz(v: number): number {
  return Math.abs(v) < DEADZONE ? 0 : v
}

export function useGamepad() {
  const [connected, setConnected] = useState(false)
  const axesRef = useRef<GamepadAxes>({ throttle: 0, yaw: 0, pitch: 0, roll: 0 })
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    const check = () => {
      const active = Array.from(navigator.getGamepads()).some(gp => gp !== null && gp.connected)
      setConnected(active)
      if (!active) axesRef.current = { throttle: 0, yaw: 0, pitch: 0, roll: 0 }
    }

    const poll = () => {
      const gp = navigator.getGamepads()[0]
      if (gp) {
        // Xbox standard mapping
        // Left stick:  axes[0]=roll X, axes[1]=pitch Y (inverted)
        // Right stick: axes[2]=yaw X,  axes[3]=throttle Y (inverted)
        axesRef.current = {
          roll:     Math.round(dz(gp.axes[0]) * 100),
          pitch:    Math.round(dz(-gp.axes[1]) * 100),
          yaw:      Math.round(dz(gp.axes[2]) * 100),
          throttle: Math.round(Math.max(0, dz(-gp.axes[3])) * 255),
        }
      }
      rafRef.current = requestAnimationFrame(poll)
    }

    check()
    window.addEventListener('gamepadconnected', check)
    window.addEventListener('gamepaddisconnected', check)
    const interval = setInterval(check, 1000)
    rafRef.current = requestAnimationFrame(poll)

    return () => {
      window.removeEventListener('gamepadconnected', check)
      window.removeEventListener('gamepaddisconnected', check)
      clearInterval(interval)
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  return { connected, axesRef }
}
