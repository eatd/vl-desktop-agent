import React, { useState, useEffect } from 'react';
import '../styles.css';

interface ClickTarget {
    x: number;
    y: number;
}

interface PreviewProps {
    jpegB64: string | null;
    clickTarget?: ClickTarget | null;
}

export function Preview({ jpegB64, clickTarget }: PreviewProps) {
    const [showMarker, setShowMarker] = useState(false);
    const [markerPos, setMarkerPos] = useState<ClickTarget | null>(null);

    useEffect(() => {
        if (clickTarget) {
            setMarkerPos(clickTarget);
            setShowMarker(true);
            const timer = setTimeout(() => setShowMarker(false), 2000);
            return () => clearTimeout(timer);
        }
    }, [clickTarget]);

    // Qwen VL uses 0-1000 normalized coordinates
    const markerStyle = markerPos ? {
        left: `${(markerPos.x / 1000) * 100}%`,
        top: `${(markerPos.y / 1000) * 100}%`,
    } : {};

    return (
        <div className="main-view">
            <div className="preview-container">
                {jpegB64 ? (
                    <>
                        <img
                            src={`data:image/jpeg;base64,${jpegB64}`}
                            alt="Live Preview"
                            className="preview-image"
                        />

                        {/* Click marker */}
                        {showMarker && markerPos && (
                            <div className="click-marker" style={markerStyle}>
                                <div className="click-marker-ring" />
                                <div className="click-marker-dot" />
                            </div>
                        )}

                        {/* Live badge */}
                        <div style={{
                            position: 'absolute',
                            top: 16,
                            right: 16,
                            background: 'rgba(0,0,0,0.7)',
                            backdropFilter: 'blur(4px)',
                            padding: '6px 10px',
                            borderRadius: 6,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            fontSize: 11,
                            fontWeight: 600,
                            color: '#ef4444',
                        }}>
                            <div style={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                background: '#ef4444',
                                boxShadow: '0 0 8px #ef4444',
                                animation: 'pulse 1.5s ease-in-out infinite',
                            }} />
                            LIVE
                        </div>
                    </>
                ) : (
                    <div className="no-signal">
                        <div className="spinner" />
                        <div style={{ fontSize: 13 }}>Waiting for preview...</div>
                        <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                            Start a goal to see live screen capture
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
