import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

interface ChatComposerProps {
  onSendMessage: (text: string) => void;
  isLoading: boolean;
}

export const ChatComposer: React.FC<ChatComposerProps> = ({
  onSendMessage,
  isLoading,
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        140
      )}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-black via-black/90 to-transparent pb-6 pt-6 px-4">
      <div className="mx-auto max-w-2xl">
        <div className="relative flex items-end rounded-2xl border border-white/[0.12] bg-[#0A0A0A] shadow-2xl backdrop-blur-xl transition-all focus-within:border-white/30">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            disabled={isLoading}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Umbrella..."
            className="w-full resize-none bg-transparent py-3.5 pl-4 pr-12 text-sm text-white placeholder-text-muted focus:outline-none disabled:opacity-50"
          />

          <button
            type="button"
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            className="absolute right-2.5 bottom-2.5 flex h-8 w-8 items-center justify-center rounded-full bg-white text-black transition-all hover:bg-white/90 disabled:opacity-30 disabled:hover:bg-white"
            title="Send"
          >
            <ArrowUp className="h-4 w-4 stroke-[2.5]" />
          </button>
        </div>
        <div className="mt-2 text-center text-[11px] text-text-muted">
          Umbrella plans actions using deterministic risk thresholds.
        </div>
      </div>
    </div>
  );
};
