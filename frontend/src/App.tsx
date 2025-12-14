import { useCallback, useEffect, useRef, useState } from 'react';
import { connectEvents, fetchStatus, runGoal, stopGoal, type AgentStatus, type EventEnvelope, type EventsConnectionState } from './api';
import { SettingsModal } from './SettingsModal';
import { ControlPanel } from './components/ControlPanel';
import { LogPanel } from './components/LogPanel';
import { Preview } from './components/Preview';
import { StatusBadge } from './components/StatusBadge';
import './styles.css';

interface ClickTarget {
  x: number;
  y: number;
}

export function App() {
  const [goal, setGoal] = useState('Open Firefox and go to youtube.com');
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [events, setEvents] = useState<EventEnvelope[]>([]);
  const [jpegB64, setJpegB64] = useState<string | null>(null);
  const [connState, setConnState] = useState<EventsConnectionState>('connecting');
  const [showSettings, setShowSettings] = useState(false);
  const [clickTarget, setClickTarget] = useState<ClickTarget | null>(null);

  const connRef = useRef<{ close: () => void } | null>(null);

  useEffect(() => {
    fetchStatus().then(setStatus).catch(() => { });
  }, []);

  useEffect(() => {
    connRef.current = connectEvents(
      (evt) => {
        // Process events for log display
        if (evt.type === 'action' || evt.type === 'error' || evt.type === 'log' || evt.type === 'status' || evt.type === 'warning') {
          setEvents((prev) => {
            const next = [...prev, evt];
            return next.slice(-200);
          });
        }

        if (evt.type === 'status') setStatus(evt.payload);
        if (evt.type === 'preview') {
          setJpegB64(evt.payload?.jpeg_b64 ?? null);
          if (evt.payload?.status) {
            setStatus((prev) => prev ? { ...prev, ...evt.payload.status } : evt.payload.status);
          }
        }

        // Handle click target from action events
        if (evt.type === 'action' && evt.payload?.click_target) {
          setClickTarget(evt.payload.click_target);
        }
      },
      (state) => {
        setConnState(state);
        const connectMsg = state === 'open' ? 'Connected to agent events' : `Connection state: ${state}`;
        setEvents((prev) => [...prev, { type: 'log', ts: Date.now() / 1000, payload: { message: connectMsg } }]);
      }
    );

    return () => connRef.current?.close();
  }, []);

  const running = status?.running ?? false;

  const onRun = useCallback(async () => {
    if (!goal.trim()) return;
    setClickTarget(null); // Clear old markers
    setEvents(p => [...p, { type: 'log', ts: Date.now() / 1000, payload: { message: `Goal started: ${goal}` } }]);
    const res = await runGoal(goal);
    if (!res.ok && res.error) {
      setEvents((prev) => [...prev, { type: 'error', ts: Date.now() / 1000, payload: { message: res.error } }]);
    }
    setStatus(res.status);
  }, [goal]);

  const onStop = useCallback(async () => {
    const res = await stopGoal();
    setEvents(p => [...p, { type: 'log', ts: Date.now() / 1000, payload: { message: 'Stop requested...' } }]);
    setStatus(res.status);
  }, []);

  return (
    <div className="app-container fade-in">
      <div className="sidebar">
        <ControlPanel
          goal={goal}
          setGoal={setGoal}
          running={running}
          onRun={onRun}
          onStop={onStop}
          onSettings={() => setShowSettings(true)}
        />

        <div className="card-glass">
          <div className="text-xs" style={{ textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Status</div>
          <div className="status-grid">
            <StatusBadge label="State" value={running ? 'BUSY' : 'IDLE'} active={running} />
            <StatusBadge label="Step" value={status?.step ?? 0} />
            <StatusBadge label="WebSock" value={connState} active={connState === 'open'} />
            <StatusBadge label="Dry Run" value={String(status?.dry_run ?? false)} />
          </div>
          {status?.last_action && (
            <StatusBadge label="Last Action" value={status.last_action} column />
          )}
        </div>

        <LogPanel events={events} />
      </div>

      <Preview jpegB64={jpegB64} clickTarget={clickTarget} />

      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  );
}
