import React from 'react';
import '../styles.css';

interface ControlPanelProps {
    goal: string;
    setGoal: (g: string) => void;
    running: boolean;
    onRun: () => void;
    onStop: () => void;
    onSettings: () => void;
}

export function ControlPanel({ goal, setGoal, running, onRun, onStop, onSettings }: ControlPanelProps) {
    return (
        <div className="card-glass">
            <div className="flex-row justify-between" style={{ marginBottom: 4 }}>
                <div>
                    <h1>VL Actions</h1>
                    <div className="text-xs" style={{ marginTop: 4 }}>Vision-Language Desktop Agent</div>
                </div>
                <button
                    onClick={onSettings}
                    style={{ background: 'transparent', padding: '8px', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
                    title="Settings"
                >
                    ⚙️
                </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <input
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    placeholder="Describe your goal..."
                    onKeyDown={(e) => e.key === 'Enter' && !running && onRun()}
                    disabled={running}
                    autoFocus
                />

                <div className="flex-row">
                    <button
                        className={`primary flex-1 ${running ? 'pulse-active' : ''}`}
                        onClick={onRun}
                        disabled={running}
                    >
                        {running ? 'Agent Running...' : 'Start Mission'}
                    </button>
                    <button
                        className="danger"
                        onClick={onStop}
                        disabled={!running}
                        style={{ padding: '10px 16px' }}
                    >
                        Stop
                    </button>
                </div>
            </div>
        </div>
    );
}
