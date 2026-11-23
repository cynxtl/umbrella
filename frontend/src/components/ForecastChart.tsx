import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { ForecastSlot } from '../types';
import { formatTemp } from '../lib/utils';

interface ForecastChartProps {
  timeline: ForecastSlot[];
  unit?: string;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  timeline,
  unit = '°C',
}) => {
  if (!timeline || timeline.length === 0) return null;

  const data = timeline.map((slot) => ({
    time: slot.time,
    pop: Math.round(slot.rain_probability * 100),
    temp: slot.temperature,
    desc: slot.description,
  }));

  return (
    <div className="w-full pt-2">
      <div className="flex items-center justify-between text-xs text-text-muted mb-2 px-1">
        <span>Rain probability curve (3h forecast blocks)</span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-risk-mod" />
            30% Moderate
          </span>
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-risk-high" />
            60% High
          </span>
        </div>
      </div>

      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
            <defs>
              <linearGradient id="rainGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#FFFFFF" stopOpacity={0.18} />
                <stop offset="100%" stopColor="#FFFFFF" stopOpacity={0.01} />
              </linearGradient>
            </defs>

            <XAxis
              dataKey="time"
              stroke="#737373"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#737373"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              ticks={[0, 30, 60, 100]}
              tickFormatter={(v) => `${v}%`}
            />

            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload;
                  return (
                    <div className="rounded-lg border border-white/10 bg-[#111111] p-2 text-xs shadow-xl backdrop-blur-md">
                      <div className="font-semibold text-white">{item.time}</div>
                      <div className="text-text-secondary mt-0.5">
                        Rain: <span className="text-white font-medium">{item.pop}%</span>
                      </div>
                      <div className="text-text-secondary">
                        Temp: <span className="text-white font-medium">{formatTemp(item.temp, unit)}</span>
                      </div>
                      <div className="text-text-muted text-[11px] mt-0.5">{item.desc}</div>
                    </div>
                  );
                }
                return null;
              }}
            />

            <ReferenceLine
              y={30}
              stroke="#E9BF72"
              strokeDasharray="4 4"
              strokeWidth={1}
            />
            <ReferenceLine
              y={60}
              stroke="#E88C8C"
              strokeDasharray="3 3"
              strokeWidth={1}
            />

            <Area
              type="monotone"
              dataKey="pop"
              stroke="#FFFFFF"
              strokeWidth={2}
              fill="url(#rainGradient)"
              dot={{ fill: '#000000', stroke: '#FFFFFF', strokeWidth: 2, r: 3 }}
              activeDot={{ fill: '#FFFFFF', stroke: '#FFFFFF', r: 5 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
