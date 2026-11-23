import React from 'react';
import { Umbrella, SlidersHorizontal, RotateCcw } from 'lucide-react';

interface HeaderProps {
  demoMode: boolean;
  demoScenario: string;
  onOpenSettings: () => void;
  onResetChat: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  demoMode,
  demoScenario,
  onOpenSettings,
  onResetChat,
}) => {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-white/[0.08] bg-black/80 px-6 py-4 backdrop-blur-md">
      <div className="flex items-center gap-2.5">
        <Umbrella className="h-5 w-5 text-white" strokeWidth={2.2} />
        <span className="text-base font-semibold tracking-tight text-white">
          umbrella.
        </span>
      </div>

      <div className="flex items-center gap-3">
        {demoMode && (
          <span className="hidden sm:inline-flex items-center rounded-full border border-white/[0.12] bg-white/[0.04] px-2.5 py-0.5 text-xs text-text-secondary font-medium">
            Demo · {demoScenario}
          </span>
        )}

        <button
          onClick={onResetChat}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.03] text-text-secondary hover:bg-white/[0.08] hover:text-white transition-colors"
          title="New Chat"
        >
          <RotateCcw className="h-4 w-4" />
        </button>

        <button
          onClick={onOpenSettings}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.03] text-text-secondary hover:bg-white/[0.08] hover:text-white transition-colors"
          title="Settings"
        >
          <SlidersHorizontal className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
};
