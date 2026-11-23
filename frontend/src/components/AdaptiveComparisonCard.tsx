import React from 'react';
import { PlanComparisonData } from '../types';
import { Sparkles, CheckCircle2 } from 'lucide-react';

interface AdaptiveComparisonCardProps {
  comparison: PlanComparisonData;
}

export const AdaptiveComparisonCard: React.FC<AdaptiveComparisonCardProps> = ({
  comparison,
}) => {
  const {
    has_better_alternative,
    original_plan,
    recommended_plan,
    risk_reduction_pp,
    why_this_plan,
  } = comparison;

  const getRiskClass = (risk: string) => {
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
    <div className="mt-3 overflow-hidden rounded-xl border border-white/[0.12] bg-white/[0.035] p-3.5 backdrop-blur-md">
      <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          {has_better_alternative ? (
            <Sparkles className="h-4 w-4 text-white" />
          ) : (
            <CheckCircle2 className="h-4 w-4 text-text-secondary" />
          )}
          <span className="text-xs font-semibold uppercase tracking-wider text-white">
            {has_better_alternative
              ? 'Lower-Risk Window Suggested'
              : 'Original Timing Confirmed'}
          </span>
        </div>

        {has_better_alternative && (
          <span className="rounded-full border border-white/20 bg-white/10 px-2 py-0.5 text-[11px] font-medium text-white">
            {risk_reduction_pp.toFixed(0)} pp risk reduction
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        <div className="rounded-lg border border-white/[0.08] bg-black/40 p-2.5">
          <div className="text-[11px] font-medium uppercase tracking-wider text-text-muted">
            Original Plan
          </div>
          <div className="text-sm font-semibold text-white mt-0.5">
            {original_plan.label}
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-lg font-bold text-white">
              {Math.round(original_plan.peak_pop * 100)}%
            </span>
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-semibold border ${getRiskClass(
                original_plan.risk_level
              )}`}
            >
              {original_plan.risk_level}
            </span>
          </div>
          <div className="mt-1 text-[11px] text-text-muted truncate">
            {original_plan.conditions}
          </div>
        </div>

        <div
          className={`rounded-lg border p-2.5 ${
            has_better_alternative
              ? 'border-white/30 bg-white/[0.06]'
              : 'border-white/[0.08] bg-black/40'
          }`}
        >
          <div className="text-[11px] font-medium uppercase tracking-wider text-text-secondary">
            {has_better_alternative ? 'Suggested Alternative' : 'Current Plan'}
          </div>
          <div className="text-sm font-semibold text-white mt-0.5">
            {recommended_plan.label}
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-lg font-bold text-white">
              {Math.round(recommended_plan.peak_pop * 100)}%
            </span>
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-semibold border ${getRiskClass(
                recommended_plan.risk_level
              )}`}
            >
              {recommended_plan.risk_level}
            </span>
          </div>
          <div className="mt-1 text-[11px] text-text-secondary truncate">
            {recommended_plan.conditions}
          </div>
        </div>
      </div>

      <p className="mt-3 text-xs leading-relaxed text-text-secondary">
        {why_this_plan}
      </p>
    </div>
  );
};
