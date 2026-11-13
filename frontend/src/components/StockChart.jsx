
import { useEffect, useRef, useState } from 'react';
import {
  createChart,
  ColorType,
  CandlestickSeries,
  HistogramSeries,
} from 'lightweight-charts';

function StockChart({ data }) {
  const chartContainerRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) {
      return;
    }

    // Chart configuration
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,

      layout: {
        background: {
          type: ColorType.Solid,
          color: '#FFFFFF',
        },
        textColor: '#334155',
      },

      grid: {
        vertLines: {
          color: '#F1F5F9',
        },
        horzLines: {
          color: '#F1F5F9',
        },
      },

      rightPriceScale: {
        borderColor: '#E2E8F0',
      },

      timeScale: {
        borderColor: '#E2E8F0',
        timeVisible: false,
      },
    });

    // Candlestick series
const candlestickSeries = chart.addSeries(CandlestickSeries, {
  upColor: '#16A34A',
  downColor: '#DC2626',
  borderUpColor: '#16A34A',
  borderDownColor: '#DC2626',
  wickUpColor: '#16A34A',
  wickDownColor: '#DC2626',
});


// Prepare historical stock data
const candleData = data.map((row) => ({
  time: row.date,
  open: Number(row.open),
  high: Number(row.high),
  low: Number(row.low),
  close: Number(row.close),
}));

// Display candlestick data
candlestickSeries.setData(candleData);

// Volume histogram
const volumeSeries = chart.addSeries(HistogramSeries, {
  priceFormat: {
    type: 'volume',
  },
  priceScaleId: '',
});

// Position volume at the bottom of the chart
chart.priceScale('').applyOptions({
  scaleMargins: {
    top: 0.8,
    bottom: 0,
  },
});

// Prepare volume data
const volumeData = data.map((row) => ({
  time: row.date,
  value: Number(row.volume),
  color: Number(row.close) >= Number(row.open)
    ? '#16A34A80'
    : '#DC262680',
}));

volumeSeries.setData(volumeData);
// Automatically fit all historical records
chart.timeScale().fitContent();
// Automatically resize chart when its container changes
const resizeObserver = new ResizeObserver((entries) => {
  const { width } = entries[0].contentRect;

  if (width > 0) {
    chart.applyOptions({ width });
  }
});

resizeObserver.observe(chartContainerRef.current);
// Listen for mouse movement over the chart
chart.subscribeCrosshairMove((param) => {
  if (!param.time || !param.point) {
    setTooltip(null);
    return;
  }

  const candle = param.seriesData.get(candlestickSeries);
  const volume = param.seriesData.get(volumeSeries);

  if (!candle) {
    setTooltip(null);
    return;
  }

  setTooltip({
    date: param.time,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
    volume: volume?.value ?? 0,
  });
});

    return () => {
  resizeObserver.disconnect();
  chart.remove();
};
  }, [data]);

  return (
  <div style={{ width: '100%' }}>

    {tooltip && (
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '12px',
        padding: '16px',
        marginBottom: '12px',
        background: '#F8FAFC',
        borderRadius: '10px',
        fontSize: '13px',
      }}>

        <div>
          <strong>Date</strong>
          <p>
            {typeof tooltip.date === 'string'
              ? tooltip.date
              : `${tooltip.date.year}-${String(tooltip.date.month).padStart(2, '0')}-${String(tooltip.date.day).padStart(2, '0')}`}
          </p>
        </div>

        <div>
          <strong>Open</strong>
          <p>{tooltip.open.toLocaleString()}</p>
        </div>

        <div>
          <strong>High</strong>
          <p>{tooltip.high.toLocaleString()}</p>
        </div>

        <div>
          <strong>Low</strong>
          <p>{tooltip.low.toLocaleString()}</p>
        </div>

        <div>
          <strong>Close</strong>
          <p>{tooltip.close.toLocaleString()}</p>
        </div>

        <div>
          <strong>Volume</strong>
          <p>{tooltip.volume.toLocaleString()}</p>
        </div>

      </div>
    )}

    <div
      ref={chartContainerRef}
      style={{
        width: '100%',
        height: '400px',
      }}
    />

  </div>
);
}

export default StockChart;
