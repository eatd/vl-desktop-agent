import React, { useEffect, useRef } from 'react';
import type { EventEnvelope } from '../api';
import '../styles.css';

interface LogPanelProps {
    events: EventEnvelope[];
}

export function LogPanel({ events }: LogPanelProps) {
    const logsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [events]);

    return (
        <div className="card-glass" style={{ flex: 1, minHeight: 0, padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '16px 16px 8px', borderBottom: '1px solid var(--border)' }}>
                <span className="text-xs">Mission Log</span>
            </div>
            <div className="log-panel">
                {events.length === 0 ? (
                    <div style={{ color: 'var(--text-dim)', textAlign: 'center', padding: 20 }}>
                        No events yet
                    </div>
                ) : (
                    events.map((e, i) => <LogItem key={i} event={e} />)
                )}
                <div ref={logsEndRef} />
            </div>
        </div>
    );
}

function LogItem({ event }: { event: EventEnvelope }) {
    const ts = event.ts || Date.now() / 1000;
    const time = new Date(ts * 1000).toLocaleTimeString([], {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    let content = '';
    let typeClass = 'dim';

    if (event.type === 'log') {
        content = event.payload?.message || '';
    } else if (event.type === 'action') {
        typeClass = 'action';
        content = event.payload?.description || `Action: ${event.payload?.action?.action || 'unknown'}`;
    } else if (event.type === 'error') {
        typeClass = 'error';
        content = event.payload?.message || 'Error';
    } else if (event.type === 'warning') {
        typeClass = 'warning';
        content = event.payload?.message || 'Warning';
    } else if (event.type === 'status') {
        return null; // Don't show status updates in log
    }

    if (!content) return null;

    return (
        <div className={`log-entry ${typeClass}`}>
            <span style={{ opacity: 0.4, marginRight: 8 }}>[{time}]</span>
            {content}
        </div>
    );
}
