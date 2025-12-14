import { useCallback, useEffect, useRef, useState } from 'react';
import { connectEvents, fetchStatus, runGoal, stopGoal, type AgentStatus, type EventEnvelope, type EventsConnectionState } from './api';
import { SettingsModal } from './SettingsModal';
import { LogPanel } from './components/LogPanel';
import { Preview } from './components/Preview';
import './styles.css';

interface ClickTarget {
  x: number;
  y: number;
}

export function App() {
  const [goal, setGoal] = useState('');
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [events, setEvents] = useState<EventEnvelope[]>([]);
  const [jpegB64, setJpegB64] = useState<string | null>(null);
  const [connState, setConnState] = useState<EventsConnectionState>('connecting');
  const [showSettings, setShowSettings] = useState(false);
  const [clickTarget, setClickTarget] = useState<ClickTarget | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const connRef = useRef<{ close: () => void } | null>(null);

  const running = status?.running ?? false;
  const maxSteps = 50;
  const progressPct = Math.min(100, ((status?.step ?? 0) / maxSteps) * 100);

  useEffect(() => {
    fetchStatus().then(setStatus).catch(() => { });
  }, []);

  useEffect(() => {
    connRef.current = connectEvents(
      (evt) => {
        if (['action', 'error', 'log', 'status', 'warning'].includes(evt.type)) {
          setEvents((prev) => [...prev, evt].slice(-100));
        }
        if (evt.type === 'status') setStatus(evt.payload);
        if (evt.type === 'preview') {
          setJpegB64(evt.payload?.jpeg_b64 ?? null);
          if (evt.payload?.status) setStatus(s => s ? { ...s, ...evt.payload.status } : evt.payload.status);
        }
        if (evt.type === 'action' && evt.payload?.click_target) {
          setClickTarget(evt.payload.click_target);
        }
      },
      (state) => {
        setConnState(state);
      }
    );
    return () => connRef.current?.close();
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && running) {
        e.preventDefault();
        onStop();
      }
      if (e.key === ',' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setShowSettings(true);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [running]);

  const onRun = useCallback(async () => {
    if (!goal.trim() || running) return;
    setClickTarget(null);
    setEvents([]);
    const res = await runGoal(goal);
    setStatus(res.status);
  }, [goal, running]);

  const onStop = useCallback(async () => {
    const res = await stopGoal();
    setStatus(res.status);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !running) {
      onRun();
    }
  };

  return (
    <div className="app-root">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <span className="logo">🤖</span>
          <h1>VL Desktop Agent</h1>
        </div>
        <div className="header-right">
          <div className={`conn-indicator ${connState === 'open' ? 'connected' : ''}`}>
            <span className="conn-dot" />
            {connState === 'open' ? 'Connected' : 'Connecting...'}
          </div>
          <button className="icon-btn" onClick={() => setShowSettings(true)} title="Settings (Ctrl+,)">
            ⚙️
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="app-main">
        {/* Left Panel */}
        <div className="left-panel">
          {/* Goal Input */}
          <div className="card-glass goal-card">
            <label className="input-label">What should I do?</label>
            <input
              ref={inputRef}
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. Open Chrome and go to youtube.com"
              disabled={running}
            />

            {/* Action Buttons */}
            <div className="action-buttons">
              {!running ? (
                <button className="btn-primary" onClick={onRun} disabled={!goal.trim()}>
                  ▶ Run Goal
                </button>
              ) : (
                <button className="btn-danger" onClick={onStop}>
                  ⏹ Stop
                </button>
              )}
            </div>

            {/* Progress Bar */}
            {running && (
              <div className="progress-container">
                <div className="progress-bar" style={{ width: `${progressPct}%` }} />
                <span className="progress-text">Step {status?.step ?? 0} / {maxSteps}</span>
              </div>
            )}
          </div>

          {/* Status Card */}
          <div className="card-glass status-card">
            <div className="status-row">
              <span className="status-label">Status</span>
              <span className={`status-value ${running ? 'active' : ''}`}>
                {running ? '🟢 Running' : '⚪ Idle'}
              </span>
            </div>
            {status?.last_action && (
              <div className="status-row">
                <span className="status-label">Last Action</span>
                <span className="status-value mono">{status.last_action}</span>
              </div>
            )}
            {status?.dry_run && (
              <div className="dry-run-badge">DRY RUN</div>
            )}
          </div>

          {/* Log Panel */}
          <LogPanel events={events} />
        </div>

        {/* Preview */}
        <Preview jpegB64={jpegB64} clickTarget={clickTarget} />
      </div>

      {/* Settings Modal */}
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}

      {/* Keyboard hints */}
      <div className="keyboard-hints">
        <span>Enter = Run</span>
        <span>Esc = Stop</span>
        <span>Ctrl+, = Settings</span>
      </div>
    </div>
  );
}
