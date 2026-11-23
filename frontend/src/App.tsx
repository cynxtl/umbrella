import { useState, useEffect, useRef } from 'react';
import { Message } from './types';
import { Header } from './components/Header';
import { WelcomeView } from './components/WelcomeView';
import { ChatComposer } from './components/ChatComposer';
import { ChatMessageItem } from './components/ChatMessageItem';
import { SettingsModal } from './components/SettingsModal';
import { Umbrella } from 'lucide-react';

export function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  // Settings
  const [demoMode, setDemoMode] = useState<boolean>(true);
  const [demoScenario, setDemoScenario] = useState<string>('Moderate');
  const [unit, setUnit] = useState<string>('°C');
  const [preference, setPreference] = useState<string>('Balanced');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Generate or load session ID
    let currentId = localStorage.getItem('umbrella_session_id');
    if (!currentId) {
      currentId = Math.random().toString(36).substring(2, 14);
      localStorage.setItem('umbrella_session_id', currentId);
    }
    setSessionId(currentId);

    // Fetch initial preferences from server
    fetch('/api/sessions/preferences')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.preference) {
          setPreference(data.preference);
        }
      })
      .catch(() => {});
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsgId = Math.random().toString(36).substring(2, 9);
    const userMsg: Message = {
      id: userMsgId,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          demo_mode: demoMode,
          demo_scenario: demoScenario,
          preference: preference,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      const assistantMsgId = Math.random().toString(36).substring(2, 9);
      const assistantMsg: Message = {
        id: assistantMsgId,
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        data: data,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errMsg: Message = {
        id: Math.random().toString(36).substring(2, 9),
        role: 'assistant',
        content:
          'Unable to reach weather service. Please check your network connection or try switching to offline demo mode.',
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetChat = async () => {
    setMessages([]);
    if (sessionId) {
      try {
        await fetch(`/api/chat/reset?session_id=${sessionId}`, {
          method: 'POST',
        });
      } catch {}
    }
  };

  const handleAdjustCaution = async (adj: number) => {
    try {
      await fetch('/api/sessions/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preference: preference,
          caution_adjustment: adj,
        }),
      });
    } catch {}
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col font-sans">
      <Header
        demoMode={demoMode}
        demoScenario={demoScenario}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onResetChat={handleResetChat}
      />

      <main className="flex-1 w-full max-w-2xl mx-auto px-4 pb-28 pt-4">
        {messages.length === 0 ? (
          <WelcomeView onSelectPrompt={handleSendMessage} />
        ) : (
          <div className="space-y-4 pt-2">
            {messages.map((msg) => (
              <ChatMessageItem key={msg.id} message={msg} unit={unit} />
            ))}

            {isLoading && (
              <div className="flex items-center gap-2.5 text-text-muted text-xs py-3 my-2">
                <Umbrella className="h-4 w-4 animate-pulse text-white" />
                <span>Evaluating weather conditions...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      <ChatComposer onSendMessage={handleSendMessage} isLoading={isLoading} />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        demoMode={demoMode}
        onToggleDemoMode={setDemoMode}
        demoScenario={demoScenario}
        onChangeDemoScenario={setDemoScenario}
        unit={unit}
        onChangeUnit={setUnit}
        preference={preference}
        onChangePreference={(p) => {
          setPreference(p);
          fetch('/api/sessions/preferences', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              preference: p,
              caution_adjustment: 0,
            }),
          }).catch(() => {});
        }}
        onAdjustCaution={handleAdjustCaution}
        onResetChat={handleResetChat}
      />
    </div>
  );
}

export default App;
