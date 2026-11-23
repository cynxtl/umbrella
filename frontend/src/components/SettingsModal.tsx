import React from 'react';
import { X, SlidersHorizontal, Trash2 } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  demoMode: boolean;
  onToggleDemoMode: (val: boolean) => void;
  demoScenario: string;
  onChangeDemoScenario: (val: string) => void;
  unit: string;
  onChangeUnit: (val: string) => void;
  preference: string;
  onChangePreference: (val: string) => void;
  onAdjustCaution: (val: number) => void;
  onResetChat: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  demoMode,
  onToggleDemoMode,
  demoScenario,
  onChangeDemoScenario,
  unit,
  onChangeUnit,
  preference,
  onChangePreference,
  onAdjustCaution,
  onResetChat,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl border border-white/[0.12] bg-[#0A0A0A] p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-2 text-white font-semibold text-sm">
            <SlidersHorizontal className="h-4 w-4" />
            <span>Preferences & Demo</span>
          </div>
          <button
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-lg text-text-muted hover:text-white transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-5 py-4">
          {/* Demo Mode */}
          <div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-white">Offline Scenario Demo</div>
                <div className="text-xs text-text-muted">
                  Use mathematically consistent local sample data
                </div>
              </div>
              <input
                type="checkbox"
                checked={demoMode}
                onChange={(e) => onToggleDemoMode(e.target.checked)}
                className="h-4 w-4 rounded border-white/20 bg-black text-white focus:ring-0"
              />
            </div>

            {demoMode && (
              <div className="mt-3 flex gap-2">
                {['Moderate', 'Low', 'High'].map((scen) => (
                  <button
                    key={scen}
                    type="button"
                    onClick={() => onChangeDemoScenario(scen)}
                    className={`flex-1 rounded-lg border py-1.5 text-xs font-medium transition-all ${
                      demoScenario === scen
                        ? 'border-white bg-white text-black font-semibold'
                        : 'border-white/10 bg-white/[0.03] text-text-secondary hover:text-white'
                    }`}
                  >
                    {scen}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Temperature Unit */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Temperature Unit
            </label>
            <div className="flex gap-2">
              {['°C', '°F'].map((u) => (
                <button
                  key={u}
                  type="button"
                  onClick={() => onChangeUnit(u)}
                  className={`flex-1 rounded-lg border py-1.5 text-xs font-medium transition-all ${
                    unit === u
                      ? 'border-white bg-white text-black font-semibold'
                      : 'border-white/10 bg-white/[0.03] text-text-secondary hover:text-white'
                  }`}
                >
                  {u}
                </button>
              ))}
            </div>
          </div>

          {/* Advice Style */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Advice Style
            </label>
            <div className="flex gap-2">
              {['Conservative', 'Balanced', 'Relaxed'].map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => onChangePreference(p)}
                  className={`flex-1 rounded-lg border py-1.5 text-xs font-medium transition-all ${
                    preference === p
                      ? 'border-white bg-white text-black font-semibold'
                      : 'border-white/10 bg-white/[0.03] text-text-secondary hover:text-white'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Feedback Memory Shift */}
          <div>
            <label className="block text-sm font-medium text-white mb-1">
              Feedback Sensitivity
            </label>
            <div className="text-xs text-text-muted mb-2">
              Temporarily shift advice style without altering baseline risk
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => onAdjustCaution(1)}
                className="flex-1 rounded-lg border border-white/10 bg-white/[0.03] py-1.5 text-xs text-text-secondary hover:text-white transition-colors"
              >
                + More Cautious
              </button>
              <button
                type="button"
                onClick={() => onAdjustCaution(0)}
                className="flex-1 rounded-lg border border-white/10 bg-white/[0.03] py-1.5 text-xs text-text-secondary hover:text-white transition-colors"
              >
                Standard
              </button>
              <button
                type="button"
                onClick={() => onAdjustCaution(-1)}
                className="flex-1 rounded-lg border border-white/10 bg-white/[0.03] py-1.5 text-xs text-text-secondary hover:text-white transition-colors"
              >
                - Less Cautious
              </button>
            </div>
          </div>

          {/* Reset Conversation */}
          <div className="pt-2 border-t border-white/[0.08]">
            <button
              type="button"
              onClick={() => {
                onResetChat();
                onClose();
              }}
              className="w-full flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] py-2 text-xs font-medium text-text-secondary hover:bg-white/[0.08] hover:text-white transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clear Current Conversation</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
