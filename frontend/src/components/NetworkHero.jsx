import { useEffect, useRef } from 'react'

// 화면 전체 배경에 깔리는 장식 애니메이션 — 노드가 서서히 떠다니다 가까워지면 선으로 연결됨
const CONNECT_DISTANCE = 120
const SPEED = 0.15
const DOT_RGB = '15, 23, 42' // slate-900 — 밝은 배경 위에 은은하게 보이도록

function NetworkHero({ className = '' }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const prefersReducedMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)',
    ).matches
    const dpr = Math.min(window.devicePixelRatio || 1, 2)

    let width = 0
    let height = 0
    let nodes = []

    // 화면 크기에 비례한 밀도로 노드 수를 정해 좁은 박스가 아닌 전체 화면에 자연스럽게 분포시킴
    const buildNodes = () => {
      const count = Math.min(
        70,
        Math.max(28, Math.round((width * height) / 16000)),
      )
      nodes = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * SPEED,
        vy: (Math.random() - 0.5) * SPEED,
      }))
    }

    const resize = () => {
      const rect = canvas.getBoundingClientRect()
      width = rect.width
      height = rect.height
      canvas.width = width * dpr
      canvas.height = height * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      buildNodes()
    }
    resize()
    window.addEventListener('resize', resize)

    let frameId

    const drawFrame = () => {
      ctx.clearRect(0, 0, width, height)

      nodes.forEach((n) => {
        n.x += n.vx
        n.y += n.vy
        if (n.x < 0 || n.x > width) n.vx *= -1
        if (n.y < 0 || n.y > height) n.vy *= -1
      })

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x
          const dy = nodes[i].y - nodes[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < CONNECT_DISTANCE) {
            ctx.strokeStyle = `rgba(${DOT_RGB}, ${0.07 * (1 - dist / CONNECT_DISTANCE)})`
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.moveTo(nodes[i].x, nodes[i].y)
            ctx.lineTo(nodes[j].x, nodes[j].y)
            ctx.stroke()
          }
        }
      }

      nodes.forEach((n) => {
        ctx.fillStyle = `rgba(${DOT_RGB}, 0.3)`
        ctx.beginPath()
        ctx.arc(n.x, n.y, 1.6, 0, Math.PI * 2)
        ctx.fill()
      })
    }

    const loop = () => {
      drawFrame()
      frameId = requestAnimationFrame(loop)
    }

    // 모션 최소화 설정을 존중해 정적인 한 프레임만 그림
    if (prefersReducedMotion) {
      drawFrame()
    } else {
      loop()
    }

    return () => {
      window.removeEventListener('resize', resize)
      if (frameId) cancelAnimationFrame(frameId)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className={`pointer-events-none ${className}`}
      aria-hidden="true"
    />
  )
}

export default NetworkHero
