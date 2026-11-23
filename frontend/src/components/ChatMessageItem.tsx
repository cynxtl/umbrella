import React, { useState } from 'react';
import { Message } from '../types';
import { Umbrella, ChevronDown, ChevronRight, BarChart3, Terminal, MapPin, Clock } from 'lucide-react';
import { formatTemp } from '../lib/utils';
import { ForecastChart } from './ForecastChart';
import { AdaptiveComparisonCard } from './AdaptiveComparisonCard';
import { AgentActivityTrace } from './AgentActivityTrace';

interface ChatMessageItemProps {
  message: Message;
  unit?: string;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  unit = '°C',
}) => {
  const [showChart, setShowChart] = useState(false);
  const [showTrace, setShowTrace] = useState(false);

  if (message.role === 'user') {
    return (
      <div className="flex justify-end my-4">
        <div className="max-w-[85%] sm:max-w-[70%] rounded-2xl bg-white/[0.08] border border-white/[0.08] px-4 py-2.5 text-sm text-white font-normal leading-relaxed">
          {message.content}
        </div>
      </div>
    );
  }

  const data = message.data;
  const riskClass = (risk: string = 'LOW') => {
    switch (risk.toUpperCase()) {
      case 'LOW':
        return 'text-risk-low border-risk-low/30 bg-risk-low/10';
      case 'MODERATE':
        return 'text-risk-mod border-risk-mod/30 bg-risk-mod/10';
      case 'HIGH':
        return 'text-risk-high border-risk-high/30 bg-risk-high/10';
      default:
        return 'text-text-secondary border-white/10 bg-white/5';
    }
  };

  return (
    <div className="flex items-start gap-3 my-5">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-white/[0.12] bg-white/[0.04] text-white">
        <Umbrella className="h-4 w-4" />
      </div>

      <div className="flex-1 min-w-0 space-y-3">
        {/* Natural conversational text */}
        <div className="text-sm text-white font-normal leading-relaxed">
          {message.content}
        </div>

        {/* Inline Weather Card */}
        {data && (
          <div className="rounded-xl border border-white/[0.10] bg-white/[0.035] p-3.5 backdrop-blur-md">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-white">
                  {data.personalized_recommendation || data.recommendation}
                </div>
                <div className="flex items-center gap-2 flex-wrap text-xs text-text-secondary mt-1">
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-text-muted" />
                    {data.plan_context?.location || 'Pune'}
                  </span>
                  <span>·</span>
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3 w-3 text-text-muted" />
                    {data.plan_context?.activity_type || 'General'} (
                    {data.plan_context?.start_time} – {data.plan_context?.end_time})
                  </span>
                  <span>·</span>
                  <span>
                    {data.conditions} · {formatTemp(data.temperature, unit)}
                  </span>
                </div>
              </div>

              <div
                className={`shrink-0 rounded px-2 py-0.5 text-[11px] font-bold border uppercase tracking-wider ${riskClass(
                  data.risk_level
                )}`}
              >
                {data.risk_level} · {Math.round(data.rain_probability * 100)}%
              </div>
            </div>
          </div>
        )}

        {/* Adaptive Plan Comparison Card if present */}
        {data?.plan_comparison && (
          <AdaptiveComparisonCard comparison={data.plan_comparison} />
        )}

        {/* Expandable Tools */}
        {data && (
          <div className="flex flex-col gap-1.5 pt-1">
            {data.forecast_timeline && data.forecast_timeline.length > 0 && (
              <div className="rounded-lg border border-white/[0.08] bg-black/40 overflow-hidden">
                <button
                  type="button"
                  onClick={() => setShowChart(!showChart)}
                  className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-text-secondary hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-3.5 w-3.5" />
                    <span>Forecast Timeline</span>
                  </div>
                  {showChart ? (
                    <ChevronDown className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5" />
                  )}
                </button>
                {showChart && (
                  <div className="px-3 pb-3 border-t border-white/[0.04]">
                    <ForecastChart timeline={data.forecast_timeline} unit={unit} />
                  </div>
                )}
              </div>
            )}

            {data.execution_trace && data.execution_trace.length > 0 && (
              <div className="rounded-lg border border-white/[0.08] bg-black/40 overflow-hidden">
                <button
                  type="button"
                  onClick={() => setShowTrace(!showTrace)}
                  className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-text-secondary hover:text-white transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Terminal className="h-3.5 w-3.5" />
                    <span>Agent Activity ({data.execution_trace.length} steps)</span>
                  </div>
                  {showTrace ? (
                    <ChevronDown className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5" />
                  )}
                </button>
                {showTrace && (
                  <div className="px-3 pb-3 border-t border-white/[0.04]">
                    <AgentActivityTrace
                      steps={data.execution_trace}
                      roles={data.roles}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
