import { useState, useEffect, useRef } from 'react';
import { Message, LocationItem } from './types';
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

  // Persistent confirmed location: null displays 'Choose location'
  const [currentLocation, setCurrentLocation] = useState<LocationItem | null>(null);

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

    // Fetch initial preferences & history from server
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

  const handleSelectLocation = async (loc: LocationItem) => {
    setCurrentLocation(loc);
    if (!sessionId) return;

    try {
      const response = await fetch('/api/chat/location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          location: loc.name,
          region: loc.region,
          country: loc.country,
          country_code: loc.country_code,
          lat: loc.lat,
          lon: loc.lon,
          display_name: loc.display_name,
          demo_mode: demoMode,
          demo_scenario: demoScenario,
        }),
      });

      if (response.ok) {
        const resData = await response.json();
        // If an active plan was recalculated, append the updated assistant message
        if (resData.recalculated && resData.message) {
          const assistantMsg: Message = {
            id: resData.message.id || Math.random().toString(36).substring(2, 9),
            role: 'assistant',
            content: resData.message.content,
            timestamp:
              resData.message.timestamp ||
              new Date().toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              }),
            data: resData.message.data,
          };
          setMessages((prev) => [...prev, assistantMsg]);
        }
      }
    } catch (err) {
      console.error('Failed to update location:', err);
    }
  };

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
          location: currentLocation ? currentLocation.name : undefined,
          demo_mode: demoMode,
          demo_scenario: demoScenario,
          preference: preference,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();

      // Synchronize confirmed location if returned from agent
      if (data && data.plan_context && data.plan_context.location) {
        if (data.plan_context.location_details) {
          setCurrentLocation(data.plan_context.location_details);
        } else if (!currentLocation || currentLocation.name !== data.plan_context.location) {
          setCurrentLocation({
            name: data.plan_context.location,
            country: 'India',
            display_name: data.plan_context.location,
          });
        }
      }

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
    setCurrentLocation(null);
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
        currentLocation={currentLocation}
        onSelectLocation={handleSelectLocation}
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
