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
        <div className="card-glass" style={{ flex: 1, minHeight: 0 }}>
            <div className="text-xs" style={{ textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                Mission Log
            </div>
            <div className="log-panel">
                {events.map((e, i) => (
                    <LogItem key={i} event={e} />
                ))}
                <div ref={logsEndRef} />
            </div>
        </div>
    );
}

function LogItem({ event }: { event: EventEnvelope }) {
    // Handle missing/invalid timestamp
    const ts = event.ts || event.payload?.ts || Date.now() / 1000;
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
        // Get action type - check both 'action' and 'action_type' fields
        const act = event.payload?.action?.action || event.payload?.action?.action_type || event.payload?.description || 'unknown';
        const desc = event.payload?.description || '';

        // Use description if available, otherwise construct from action
        if (desc) {
            content = desc;
        } else {
            content = `Action: ${act}`;
        }
    } else if (event.type === 'error') {
        typeClass = 'error';
        content = event.payload?.message || 'Error';
    } else if (event.type === 'warning') {
        typeClass = 'warning';
        content = event.payload?.message || 'Warning';
    } else if (event.type === 'status') {
        typeClass = 'status';
        content = 'Status update';
    }

    if (!content) return null;

    return (
        <div className={`log-entry ${typeClass}`}>
            <span style={{ opacity: 0.4, marginRight: 8 }}>[{time}]</span>
            {content}
        </div>
    );
}
