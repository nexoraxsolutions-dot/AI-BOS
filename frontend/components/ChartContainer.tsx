"use client"

import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'

/* ============================================================
   ChartContainer — a card wrapper for any chart with a
   title, optional subtitle, and an optional action node.
   ============================================================ */
interface ChartContainerProps {
  title: string
  subtitle?: string
  action?: React.ReactNode
  className?: string
  children: React.ReactNode
}

export function ChartContainer({
  title,
  subtitle,
  action,
  className = '',
  children,
}: ChartContainerProps) {
  return (
    <div className={['card p-5 sm:p-6', className].join(' ')}>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-dark-text">{title}</h3>
          {subtitle && (
            <p className="mt-0.5 text-sm text-slate-500 dark:text-dark-muted">{subtitle}</p>
          )}
        </div>
        {action}
      </div>
      {children}
    </div>
  )
}

/* ============================================================
   AreaChart — smooth dual line/area chart (Revenue vs Deals).
   Pure SVG, responsive via viewBox, with interactive tooltips.
   ============================================================ */
export interface AreaChartSeries {
  name: string
  color: string // hex, e.g. "#8B5CF6"
  values: number[]
}

interface AreaChartProps {
  series: AreaChartSeries[]
  labels: string[]
  height?: number
  formatValue?: (v: number) => string
}

const VIEW_W = 640

function buildSmoothPath(pts: { x: number; y: number }[]): string {
  if (pts.length === 0) return ''
  if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`
  let d = `M ${pts[0].x} ${pts[0].y}`
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i]
    const p1 = pts[i]
    const p2 = pts[i + 1]
    const p3 = pts[i + 2] || p2
    const cp1x = p1.x + (p2.x - p0.x) / 6
    const cp1y = p1.y + (p2.y - p0.y) / 6
    const cp2x = p2.x - (p3.x - p1.x) / 6
    const cp2y = p2.y - (p3.y - p1.y) / 6
    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`
  }
  return d
}

export function AreaChart({
  series,
  labels,
  height = 240,
  formatValue = (v) => v.toString(),
}: AreaChartProps) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null)

  const geometry = useMemo(() => {
    const padL = 8
    const padR = 8
    const padT = 12
    const padB = 26
    const innerW = VIEW_W - padL - padR
    const innerH = height - padT - padB

    const allVals = series.flatMap((s) => s.values)
    const dataMax = Math.max(...allVals, 1)
    const dataMin = Math.min(...allVals, 0)
    const range = dataMax - dataMin || 1
    const max = dataMax + range * 0.12
    const min = dataMin

    const n = labels.length
    const xFor = (i: number) => padL + (n === 1 ? innerW / 2 : (i / (n - 1)) * innerW)
    const yFor = (v: number) => padT + (1 - (v - min) / (max - min)) * innerH

    const gridLines = 4
    const gridY = Array.from({ length: gridLines + 1 }, (_, i) => {
      const v = min + (range * i) / gridLines
      return { y: yFor(v), label: formatValue(Math.round(v)) }
    })

    const paths = series.map((s) => {
      const pts = s.values.map((v, i) => ({ x: xFor(i), y: yFor(v) }))
      const line = buildSmoothPath(pts)
      const area = `${line} L ${pts[pts.length - 1].x} ${padT + innerH} L ${pts[0].x} ${padT + innerH} Z`
      return { ...s, pts, line, area }
    })

    return { padL, padR, padT, padB, innerW, innerH, xFor, yFor, gridY, paths, n }
  }, [series, labels, height, formatValue])

  const { padT, innerH, xFor, gridY, paths, n } = geometry

  const handleMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const relX = ((e.clientX - rect.left) / rect.width) * VIEW_W
    const i = Math.round(((relX - 8) / geometry.innerW) * (n - 1))
    setHoverIdx(Math.max(0, Math.min(n - 1, i)))
  }

  return (
    <div className="relative w-full">
      <svg
        viewBox={`0 0 ${VIEW_W} ${height}`}
        width="100%"
        height={height}
        onMouseMove={handleMove}
        onMouseLeave={() => setHoverIdx(null)}
        className="overflow-visible"
      >
        <defs>
          {paths.map((p, i) => (
            <linearGradient key={i} id={`area-grad-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={p.color} stopOpacity="0.28" />
              <stop offset="100%" stopColor={p.color} stopOpacity="0" />
            </linearGradient>
          ))}
        </defs>

        {/* Grid */}
        {gridY.map((g, i) => (
          <g key={i}>
            <line
              x1={8}
              x2={VIEW_W - 8}
              y1={g.y}
              y2={g.y}
              stroke="currentColor"
              strokeWidth="1"
              className="text-slate-200 dark:text-slate-700/60"
            />
            <text x={4} y={g.y - 4} fontSize="9" className="fill-slate-400 dark:fill-dark-muted">
              {g.label}
            </text>
          </g>
        ))}

        {/* Areas + lines */}
        {paths.map((p, i) => (
          <g key={i}>
            <motion.path
              d={p.area}
              fill={`url(#area-grad-${i})`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
            />
            <motion.path
              d={p.line}
              fill="none"
              stroke={p.color}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1, ease: 'easeInOut', delay: i * 0.1 }}
            />
          </g>
        ))}


        {/* X labels */}
        {labels.map((l, i) => (
          <text
            key={i}
            x={xFor(i)}
            y={height - 6}
            fontSize="9"
            textAnchor="middle"
            className="fill-slate-400 dark:fill-dark-muted"
          >
            {l}
          </text>
        ))}

        {/* Hover guide + dots */}
        {hoverIdx !== null && (
          <g>
            <line
              x1={xFor(hoverIdx)}
              x2={xFor(hoverIdx)}
              y1={padT}
              y2={padT + innerH}
              stroke="currentColor"
              strokeWidth="1"
              strokeDasharray="3 3"
              className="text-slate-300 dark:text-slate-600"
            />
            {paths.map((p, i) => (
              <circle
                key={i}
                cx={p.pts[hoverIdx].x}
                cy={p.pts[hoverIdx].y}
                r="4"
                fill="#fff"
                stroke={p.color}
                strokeWidth="2.5"
              />
            ))}
          </g>
        )}
      </svg>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap items-center gap-4">
        {series.map((s, i) => (
          <div key={i} className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-dark-muted">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} />
            {s.name}
          </div>
        ))}
      </div>

      {/* Tooltip */}
      {hoverIdx !== null && (
        <div
          className="pointer-events-none absolute z-10 -translate-x-1/2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-cardLg dark:border-dark-border dark:bg-dark-surface"
          style={{ left: `${(xFor(hoverIdx) / VIEW_W) * 100}%`, top: 0 }}
        >
          <p className="mb-1 font-semibold text-slate-900 dark:text-dark-text">{labels[hoverIdx]}</p>
          {series.map((s, i) => (
            <p key={i} className="flex items-center gap-1.5 text-slate-600 dark:text-dark-muted">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
              {s.name}:{' '}
              <span className="font-medium text-slate-900 dark:text-dark-text">
                {formatValue(s.values[hoverIdx])}
              </span>
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

/* ============================================================
   DonutChart — Revenue by Source donut with legend.
   ============================================================ */
export interface DonutSegment {
  label: string
  value: number
  color: string // hex
}

interface DonutChartProps {
  data: DonutSegment[]
  size?: number
  thickness?: number
  centerLabel?: string
  centerValue?: string
}

export function DonutChart({
  data,
  size = 180,
  thickness = 22,
  centerLabel = '',
  centerValue = '',
}: DonutChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0) || 1
  const r = (size - thickness) / 2
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * r

  let accumulated = 0
  const segments = data.map((d) => {
    const pct = d.value / total
    const len = pct * circumference
    const seg = {
      ...d,
      pct,
      len,
      dasharray: `${len} ${circumference - len}`,
      dashoffset: -accumulated,
    }
    accumulated += len
    return seg
  })

  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-center sm:gap-6">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Track */}
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            strokeWidth={thickness}
            className="stroke-slate-100 dark:stroke-slate-800"
          />
          {segments.map((s, i) => (
            <motion.circle
              key={i}
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={thickness}
              strokeDasharray={s.dasharray}
              strokeDashoffset={s.dashoffset}
              transform={`rotate(-90 ${cx} ${cy})`}
              strokeLinecap="butt"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
            />
          ))}
        </svg>
        {centerValue && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xl font-semibold text-slate-900 dark:text-dark-text">
              {centerValue}
            </span>
            {centerLabel && (
              <span className="text-xs text-slate-400 dark:text-dark-muted">{centerLabel}</span>
            )}
          </div>
        )}
      </div>

      {/* Legend / breakdown */}
      <div className="grid w-full grid-cols-1 gap-2.5">
        {segments.map((s, i) => (
          <div key={i} className="flex items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} />
              <span className="text-slate-600 dark:text-dark-muted">{s.label}</span>
            </div>
            <span className="font-medium text-slate-900 dark:text-dark-text">
              {Math.round(s.pct * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

