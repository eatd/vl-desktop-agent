
import React, { useEffect, useState } from 'react';
import { fetchSettings, updateSettings } from './api';

type SettingsModalProps = {
    onClose: () => void;
};

export function SettingsModal({ onClose }: SettingsModalProps) {
    const [settings, setSettings] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchSettings()
            .then((data) => {
                setSettings(data.settings);
                setLoading(false);
            })
            .catch((err) => {
                setError(err.message);
                setLoading(false);
            });
    }, []);

    const handleChange = (key: string, value: any) => {
        setSettings((prev) => ({ ...prev, [key]: value }));
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            const res = await updateSettings(settings);
            if (res.ok) {
                onClose();
            } else {
                setError(res.error || 'Failed to save');
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading && Object.keys(settings).length === 0) {
        return (
            <div className="modal-overlay">
                <div className="card-glass" style={{ width: 400, alignItems: 'center' }}>
                    <div className="spinner" />
                </div>
            </div>
        );
    }

    return (
        <div className="modal-overlay">
            <div className="card-glass settings-modal" style={{ maxWidth: 600, width: '90%', maxHeight: '90vh', overflowY: 'auto' }}>
                <h2>Agent Settings</h2>

                {error && <div className="text-sm" style={{ color: 'var(--danger)', marginBottom: 10 }}>{error}</div>}

                <div className="settings-group">
                    <label>Agent Mode</label>
                    <select
                        value={settings.mode || 'normal'}
                        onChange={(e) => handleChange('mode', e.target.value)}
                    >
                        <option value="fast">Fast (0.3s settle)</option>
                        <option value="normal">Normal (0.7s settle)</option>
                        <option value="careful">Careful (1.2s settle)</option>
                    </select>
                    <div className="text-xs">Controls how fast the agent acts. Faster = higher risk of errors.</div>
                </div>

                <div className="settings-group">
                    <label>Model ID</label>
                    <input
                        value={settings.model || ''}
                        onChange={(e) => handleChange('model', e.target.value)}
                    />
                </div>

                <div className="settings-group">
                    <label>API Base URL</label>
                    <input
                        value={settings.base_url || ''}
                        onChange={(e) => handleChange('base_url', e.target.value)}
                    />
                </div>

                <div className="settings-grid">
                    <div className="settings-group">
                        <label>Max Steps</label>
                        <input
                            type="number"
                            value={settings.max_steps || 80}
                            onChange={(e) => handleChange('max_steps', parseInt(e.target.value))}
                        />
                    </div>
                    <div className="settings-group">
                        <label>Loop Delay (s)</label>
                        <input
                            type="number" step="0.01"
                            value={settings.loop_delay_seconds || 0.05}
                            onChange={(e) => handleChange('loop_delay_seconds', parseFloat(e.target.value))}
                        />
                    </div>
                </div>

                <div className="settings-group checkbox">
                    <label>
                        <input
                            type="checkbox"
                            checked={settings.dry_run || false}
                            onChange={(e) => handleChange('dry_run', e.target.checked)}
                        />
                        Dry Run Mode
                    </label>
                    <div className="text-xs">If enabled, actions are logged but not executed. (Safe mode)</div>
                </div>

                <div className="settings-group checkbox">
                    <label>
                        <input
                            type="checkbox"
                            checked={settings.use_grid_overlay || false}
                            onChange={(e) => handleChange('use_grid_overlay', e.target.checked)}
                        />
                        Show Grid Overlay
                    </label>
                    <div className="text-xs">Helps smaller models (4B) localize elements better.</div>
                </div>

                <div className="buttons" style={{ marginTop: 20, display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                    <button onClick={onClose} style={{ background: 'transparent', border: '1px solid var(--border)' }}>Cancel</button>
                    <button className="primary" onClick={handleSave}>Save Changes</button>
                </div>
            </div>
        </div>
    );
}
