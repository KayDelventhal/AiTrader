import { useEffect, useRef } from 'react'
import { createChart, CandlestickSeries, LineSeries, HistogramSeries, ColorType, type IChartApi, type ISeriesApi, type UTCTimestamp, type Time } from 'lightweight-charts'
import type { MarketData, Annotation, Point } from '../../client/api'

export function MarketChart({ data, indicator = 'sma', annotations = [], height = 360 }: { data: MarketData; indicator?: string; annotations?: Annotation[]; height?: number }) {
  const container = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeRef = useRef<ISeriesApi<'Histogram'> | null>(null)
  const extras = useRef<ISeriesApi<'Line'>[]>([])
  const lines = useRef<ReturnType<ISeriesApi<'Candlestick'>['createPriceLine']>[]>([])
  const first = useRef(true)
  useEffect(() => {
    const chart = createChart(container.current!, { autoSize: true, height, layout: { background: { type: ColorType.Solid, color: '#101721' }, textColor: '#8291a5', fontFamily: 'Inter, Segoe UI, sans-serif', fontSize: 11, attributionLogo: true }, grid: { vertLines: { color: '#1a2431' }, horzLines: { color: '#1a2431' } }, rightPriceScale: { borderColor: '#263142' }, timeScale: { borderColor: '#263142', timeVisible: false }, crosshair: { mode: 0 }, localization: { locale: 'en-GB' } })
    const candles = chart.addSeries(CandlestickSeries, { upColor: '#4ed0a6', downColor: '#d17a8b', borderVisible: false, wickUpColor: '#4ed0a6', wickDownColor: '#d17a8b' })
    const volume = chart.addSeries(HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: 'volume' })
    volume.priceScale().applyOptions({ scaleMargins: { top: 0.84, bottom: 0 } })
    candles.priceScale().applyOptions({ scaleMargins: { top: 0.08, bottom: 0.22 } })
    chartRef.current = chart; candleRef.current = candles; volumeRef.current = volume; first.current = true
    return () => { chart.remove(); chartRef.current = null; extras.current = []; lines.current = [] }
  }, [height])
  useEffect(() => {
    if (!chartRef.current || !candleRef.current) return
    candleRef.current.setData(data.bars.map(b => ({ ...b, time: b.time as UTCTimestamp })))
    volumeRef.current!.setData(data.bars.map(b => ({ time: b.time as UTCTimestamp, value: b.volume, color: b.close >= b.open ? '#4ed0a626' : '#d17a8b26' })))
    extras.current.forEach(s => chartRef.current!.removeSeries(s)); extras.current = []
    const series: [string, string][] = indicator === 'bollinger' ? [['upper', '#8ea8d8'], ['lower', '#8ea8d8']] : indicator === 'ema' ? [['ema20', '#d9ba79']] : indicator === 'sma' ? [['sma20', '#d9ba79'], ['sma50', '#8098de']] : indicator === 'rsi' ? [['rsi', '#b3a0ed']] : indicator === 'macd' ? [['macd', '#6fcfbe'], ['signal', '#d9ba79']] : []
    series.forEach(([name, color]) => {
      const pane = ['rsi', 'macd'].includes(indicator) ? 1 : 0
      const s = chartRef.current!.addSeries(LineSeries, { color, lineWidth: 1, priceLineVisible: false, lastValueVisible: false }, pane)
      s.setData((data.indicators[name] || []).map(p => ({ ...p, time: p.time as UTCTimestamp }))); extras.current.push(s)
    })
    if (first.current && data.bars.length) { chartRef.current.timeScale().fitContent(); first.current = false }
  }, [data, indicator])
  useEffect(() => {
    if (!candleRef.current) return
    lines.current.forEach(line => candleRef.current!.removePriceLine(line))
    lines.current = annotations.map(a => candleRef.current!.createPriceLine({ price: Number(a.price), color: '#e4bb73', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'Your level' }))
  }, [annotations])
  return <div ref={container} className="market-chart" style={{ height }} aria-label="Fictional daily candlestick chart"/>
}

export function EquityChart({ points, benchmark }: { points: Point[]; benchmark?: Point[] }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const chart = createChart(ref.current!, { autoSize: true, height: 220, layout: { background: { type: ColorType.Solid, color: '#101721' }, textColor: '#8a98ab', attributionLogo: true }, grid: { vertLines: { visible: false }, horzLines: { color: '#1d2735' } }, timeScale: { borderColor: '#273243' }, rightPriceScale: { borderColor: '#273243' } })
    const series = chart.addSeries(LineSeries, { color: '#4ed0a6', lineWidth: 2, priceLineVisible: false })
    series.setData(points.map(p => ({ ...p, time: p.time as Time })))
    if (benchmark) { const b = chart.addSeries(LineSeries, { color: '#77869f', lineWidth: 1, priceLineVisible: false }); b.setData(benchmark.map(p => ({ ...p, time: p.time as Time }))) }
    chart.timeScale().fitContent(); return () => chart.remove()
  }, [points, benchmark])
  return <div ref={ref} style={{ height: 220 }} aria-label="Backtest equity curve"/>
}
