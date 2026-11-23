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
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const canSubmit = input.trim().length > 0 && !isLoading;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-black via-black/95 to-transparent pb-6 pt-8 px-4">
      <div className="mx-auto max-w-2xl">
        <div className="relative flex items-end rounded-2xl border border-white/[0.12] bg-[#0A0A0A] shadow-2xl backdrop-blur-xl transition-all focus-within:border-white/30 focus-within:ring-1 focus-within:ring-white/20">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            disabled={isLoading}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Umbrella..."
            className="w-full resize-none bg-transparent py-3.5 pl-4 pr-12 text-sm text-white placeholder:text-text-muted focus:outline-none disabled:opacity-50"
            aria-label="Message Umbrella"
          />

          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`absolute right-2.5 bottom-2.5 flex h-8 w-8 items-center justify-center rounded-full transition-all ${
              canSubmit
                ? 'bg-white text-black hover:bg-white/90 active:scale-95 shadow-md cursor-pointer'
                : 'bg-white/[0.08] text-text-muted cursor-not-allowed opacity-60'
            }`}
            title="Send message"
            aria-label="Send message"
          >
            <ArrowUp className="h-4 w-4 stroke-[2.5]" />
          </button>
        </div>
      </div>
    </div>
  );
};
