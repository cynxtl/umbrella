import React, { useState } from 'react';
import { ExecutionStep } from '../types';
import { Check, ChevronDown, ChevronRight, Activity } from 'lucide-react';

interface AgentActivityTraceProps {
  steps: ExecutionStep[];
  roles?: Record<string, any>;
}

export const AgentActivityTrace: React.FC<AgentActivityTraceProps> = ({
  steps,
  roles,
}) => {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="w-full pt-1 pb-1">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary mb-2.5">
        <Activity className="h-3.5 w-3.5 text-white" />
        <span>Execution Timeline</span>
      </div>

      <div className="space-y-1.5">
        {steps.map((step) => {
          const isExpanded = expandedStep === step.step;
          return (
            <div
              key={step.step}
              className="rounded-lg border border-white/[0.06] bg-black/40 text-xs overflow-hidden"
            >
              <button
                type="button"
                onClick={() => setExpandedStep(isExpanded ? null : step.step)}
                className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-white/[0.03] transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-white/10 text-[10px] font-bold text-white">
                    {step.step}
                  </span>
                  <span className="font-medium text-white">{step.title}</span>
                  <span className="text-text-muted text-[11px]">
                    ({step.tool_or_node})
                  </span>
                </div>

                <div className="flex items-center gap-2 text-text-muted text-[11px]">
                  <span>{step.duration_ms.toFixed(1)}ms</span>
                  <Check className="h-3.5 w-3.5 text-risk-low" />
                  {isExpanded ? (
                    <ChevronDown className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5" />
                  )}
                </div>
              </button>

              {isExpanded && (
                <div className="px-3 pb-2.5 pt-1 text-[11px] text-text-secondary border-t border-white/[0.04] bg-white/[0.01]">
                  {step.inputs && (
                    <div className="mb-1">
                      <span className="text-text-muted font-medium">Inputs: </span>
                      <code className="text-white/80">{JSON.stringify(step.inputs)}</code>
                    </div>
                  )}
                  {step.outputs && (
                    <div>
                      <span className="text-text-muted font-medium">Outputs: </span>
                      <code className="text-white/80">{JSON.stringify(step.outputs)}</code>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {roles && (
        <div className="mt-3 pt-2.5 border-t border-white/[0.06]">
          <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider mb-1.5">
            Specialist Roles Collaboration
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div className="rounded border border-white/[0.06] bg-black/40 p-2 text-[11px]">
              <div className="font-semibold text-white">01. Forecast Analyst</div>
              <div className="text-text-muted truncate mt-0.5">
                {roles.forecast_analyst?.conditions || 'Facts extracted'}
              </div>
            </div>
            <div className="rounded border border-white/[0.06] bg-black/40 p-2 text-[11px]">
              <div className="font-semibold text-white">02. Risk Assessor</div>
              <div className="text-text-muted truncate mt-0.5">
                {roles.risk_assessor?.risk_level} Risk (Deterministic)
              </div>
            </div>
            <div className="rounded border border-white/[0.06] bg-black/40 p-2 text-[11px]">
              <div className="font-semibold text-white">03. Planning Coordinator</div>
              <div className="text-text-muted truncate mt-0.5">
                {roles.planning_coordinator?.effective_preference} Style
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
