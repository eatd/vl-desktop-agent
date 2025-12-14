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

    // Show marker when new click target arrives, auto-hide after 2s
    useEffect(() => {
        if (clickTarget) {
            setMarkerPos(clickTarget);
            setShowMarker(true);
            const timer = setTimeout(() => setShowMarker(false), 2000);
            return () => clearTimeout(timer);
        }
    }, [clickTarget]);

    // Qwen VL uses 0-1000 normalized coordinates
    // Convert to percentage for CSS positioning
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

                        {/* Click target marker */}
                        {showMarker && markerPos && (
                            <div
                                className="click-marker"
                                style={markerStyle}
                            >
                                <div className="click-marker-ring" />
                                <div className="click-marker-dot" />
                            </div>
                        )}

                        {/* Live indicator */}
                        <div style={{
                            position: 'absolute', top: 16, right: 16,
                            background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
                            padding: '4px 10px', borderRadius: 4,
                            border: '1px solid rgba(255,255,255,0.1)',
                            display: 'flex', alignItems: 'center', gap: 6,
                            fontSize: 11, fontWeight: 600, color: '#ef4444',
                            textTransform: 'uppercase', pointerEvents: 'none'
                        }}>
                            <div style={{
                                width: 8, height: 8, borderRadius: '50%',
                                background: '#ef4444', boxShadow: '0 0 8px #ef4444',
                                animation: 'pulse 1.5s ease-in-out infinite'
                            }} />
                            Live
                        </div>
                    </>
                ) : (
                    <div className="no-signal">
                        <div className="spinner"></div>
                        <div style={{ fontSize: 13, fontWeight: 500, marginTop: 12 }}>
                            Connecting to Vision...
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
