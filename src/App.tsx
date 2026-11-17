import { AlertCircle, X } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { LoadingOverlay } from './components/LoadingOverlay';
import { MenuScreen } from './components/MenuScreen';
import { ResultScreen } from './components/ResultScreen';
import { StartScreen } from './components/StartScreen';
import { TopBar } from './components/TopBar';
import type { DifyData, DifyProxyResponse } from './types/dify';

const SESSION_STORAGE_KEY = 'frywise_conversation_id';

export default function App() {
  const [conversationId, setConversationId] = useState<string>('');
  const [data, setData] = useState<DifyData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeCommand, setActiveCommand] = useState<string | null>('MENU');
  const [errorToast, setErrorToast] = useState<string | null>(null);

  const conversationIdRef = useRef<string>('');
  conversationIdRef.current = conversationId;

  const sendCommand = useCallback(async (query: string, overrideConversationId?: string) => {
    setIsLoading(true);
    setActiveCommand(query);
    setErrorToast(null);

    try {
      const convIdToSend =
        overrideConversationId !== undefined
          ? overrideConversationId
          : conversationIdRef.current;

      const response = await fetch('/api/dify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          ...(convIdToSend ? { conversation_id: convIdToSend } : {}),
        }),
      });

      const payload = (await response.json()) as DifyProxyResponse;

      if (!response.ok || payload.error) {
        throw new Error(payload.error || `Request failed (HTTP ${response.status})`);
      }

      if (payload.conversation_id) {
        setConversationId(payload.conversation_id);
        conversationIdRef.current = payload.conversation_id;
        try {
          sessionStorage.setItem(SESSION_STORAGE_KEY, payload.conversation_id);
        } catch {
          // Ignore storage quota errors
        }
      }

      if (!payload.data || (payload.data.type !== 'state' && payload.data.type !== 'result')) {
        throw new Error('Unexpected response format from Dify.');
      }

      setData(payload.data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unable to reach Dify chatflow.';
      setErrorToast(msg);
    } finally {
      setIsLoading(false);
      setActiveCommand(null);
    }
  }, []);

  // On page load: call /api/dify with query "MENU" and no conversation_id
  useEffect(() => {
    void sendCommand('MENU', '');
  }, [sendCommand]);

  return (
    <div className="min-h-screen bg-[#FFF8E7] text-[#27251F] flex flex-col">
      <TopBar
        clock={data?.clock}
        vats={data?.vats}
        disclaimer={data?.disclaimer}
        isLoading={isLoading}
        onReset={() => sendCommand('RESET')}
      />

      {/* Red Error Toast */}
      {errorToast && (
        <div
          role="alert"
          className="fixed bottom-6 right-6 z-50 max-w-md bg-[#C8102E] text-white rounded-2xl shadow-xl px-5 py-4 flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="flex-1 text-sm font-medium leading-snug">{errorToast}</div>
          <button
            type="button"
            onClick={() => setErrorToast(null)}
            className="min-w-[36px] min-h-[36px] rounded-xl hover:bg-white/15 flex items-center justify-center shrink-0 cursor-pointer"
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Full-screen Loading Overlay (with 4-step SUBMIT progress animation) */}
      <LoadingOverlay visible={isLoading} command={activeCommand} />

      <main className="flex-1">
        {!data && !isLoading && (
          <div className="min-h-[60vh] flex items-center justify-center px-4">
            <div className="bg-white border border-[#E5DDD0] rounded-2xl p-6 max-w-md w-full text-center space-y-4">
              <p className="font-display font-bold text-lg text-[#27251F]">
                No state received from Dify
              </p>
              <button
                type="button"
                onClick={() => sendCommand('MENU', '')}
                className="min-h-[56px] px-6 py-3 rounded-2xl bg-[#D62300] hover:bg-[#B81D00] text-white font-display font-bold text-base cursor-pointer"
              >
                Retry MENU
              </button>
            </div>
          </div>
        )}

        {data?.type === 'state' && data.screen === 'start' && (
          <StartScreen data={data} isLoading={isLoading} onCommand={sendCommand} />
        )}

        {data?.type === 'state' && data.screen === 'menu' && (
          <MenuScreen data={data} isLoading={isLoading} onCommand={sendCommand} />
        )}

        {data?.type === 'result' && (
          <ResultScreen data={data} isLoading={isLoading} onCommand={sendCommand} />
        )}
      </main>
    </div>
  );
}
