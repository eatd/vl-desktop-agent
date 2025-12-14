
import React from 'react';
import '../styles.css';

interface StatusBadgeProps {
    label: string;
    value: string | number;
    active?: boolean;
    column?: boolean;
}

export function StatusBadge({ label, value, active, column }: StatusBadgeProps) {
    return (
        <div
            className={`badge ${column ? 'flex-col items-start gap-1 h-auto' : ''} ${active ? 'active-border' : ''} `}
            style={column ? { flexDirection: 'column', alignItems: 'flex-start', gap: 4 } : {}}
        >
            <span className="badge-label">{label}</span>
            <span className={`badge - value ${active ? 'active' : ''} `}>{value}</span>
        </div>
    );
}
