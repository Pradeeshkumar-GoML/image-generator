import { useState, useRef, useCallback, useEffect } from 'react';
import { generateImage, generateVideo } from './api';
import type { HistoryItem, MediaType, GenerationStatus } from './types';

/* ── Example prompts ───────────────────────────────────────── */
const IMAGE_EXAMPLES = [
  'A neon-lit cyberpunk city at night with flying cars',
  'Serene Japanese garden in autumn watercolor style',
  'Astronaut surfing on saturn\'s rings, cinematic',
  'Close-up of a mechanical butterfly, steampunk',
];

const VIDEO_EXAMPLES = [
  'Timelapse of clouds swirling over mountain peaks',
  'Golden koi fish swimming in crystal clear water',
  'Neon jellyfish dancing in deep ocean darkness',
  'Cherry blossom petals falling in slow motion',
];

/* ── Toast hook ─────────────────────────────────────────────── */
interface Toast { id: string; message: string; type: 'success' | 'error' }

function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((message: string, type: Toast['type'] = 'success') => {
    const id = Math.random().toString(36).slice(2);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500);
  }, []);
  return { toasts, push };
}

/* ── App ────────────────────────────────────────────────────── */
export default function App() {
  const [activeTab, setActiveTab] = useState<MediaType>('image');
  const [prompt, setPrompt] = useState('');
  const [status, setStatus] = useState<GenerationStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ type: MediaType; url: string } | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const { toasts, push: pushToast } = useToasts();
  const resultRef = useRef<HTMLDivElement>(null);

  const examples = activeTab === 'image' ? IMAGE_EXAMPLES : VIDEO_EXAMPLES;
  const maxLen = 4000;
  const charWarn = prompt.length > maxLen * 0.85;

  useEffect(() => {
    return () => {
      history.forEach(h => URL.revokeObjectURL(h.objectUrl));
    };
  }, []); // eslint-disable-line

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setStatus('loading');
    setError(null);
    setResult(null);

    try {
      let url: string;
      if (activeTab === 'image') {
        const res = await generateImage(prompt.trim());
        url = res.objectUrl;
      } else {
        const res = await generateVideo(prompt.trim());
        url = res.objectUrl;
      }

      setResult({ type: activeTab, url });
      setStatus('success');

      const item: HistoryItem = {
        id: Math.random().toString(36).slice(2),
        type: activeTab,
        prompt: prompt.trim(),
        objectUrl: url,
        createdAt: Date.now(),
      };
      setHistory(prev => [item, ...prev].slice(0, 12));

      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Something went wrong';
      setError(msg);
      setStatus('error');
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const ext = result.type === 'image' ? 'png' : 'mp4';
    const a = document.createElement('a');
    a.href = result.url;
    a.download = `aimatic-${result.type}-${Date.now()}.${ext}`;
    a.click();
    pushToast('Download started!', 'success');
  };

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(prompt).then(() => pushToast('Prompt copied!', 'success'));
  };

  const handleClearHistory = () => {
    history.forEach(h => URL.revokeObjectURL(h.objectUrl));
    setHistory([]);
    pushToast('History cleared', 'success');
  };

  const handleHistoryClick = (item: HistoryItem) => {
    setActiveTab(item.type);
    setPrompt(item.prompt);
    setResult({ type: item.type, url: item.objectUrl });
    setStatus('success');
    setError(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="app-wrapper">
      <div className="bg-grid" />
      <div className="bg-orbs">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <header className="header">
        <div className="logo">
          <div className="logo-icon">✦</div>
          <span className="logo-text">AI Matic</span>
        </div>
        <span className="header-badge">Powered by Multi-AI</span>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="hero-eyebrow">
            <span className="dot" />
            Generative AI Studio
          </div>
          <h1 className="hero-title">
            Turn words into<br />
            <span className="gradient-text">stunning visuals</span>
          </h1>
          <p className="hero-subtitle">
            Describe anything — our AI transforms your prompt into high-quality images
            and videos in seconds.
          </p>
        </section>

        <div className="tabs">
          <button
            id="tab-image"
            className={`tab-btn${activeTab === 'image' ? ' active' : ''}`}
            onClick={() => { setActiveTab('image'); setError(null); setResult(null); setStatus('idle'); }}
          >
            🖼 Image
          </button>
          <button
            id="tab-video"
            className={`tab-btn${activeTab === 'video' ? ' active' : ''}`}
            onClick={() => { setActiveTab('video'); setError(null); setResult(null); setStatus('idle'); }}
          >
            🎬 Video
          </button>
        </div>

        <div className="generator-card">
          <label className="generator-label" htmlFor="prompt-input">
            Your Prompt
          </label>

          <div className="prompt-area">
            <textarea
              id="prompt-input"
              className="prompt-textarea"
              placeholder={
                activeTab === 'image'
                  ? 'Describe the image you want to create…'
                  : 'Describe the video scene you want to generate…'
              }
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              maxLength={maxLen}
              rows={4}
              onKeyDown={e => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleGenerate();
              }}
            />
            <span className={`char-count${charWarn ? ' warn' : ''}`}>
              {prompt.length}/{maxLen}
            </span>
          </div>

          <div className="example-prompts">
            <div className="example-prompts-title">Try an example</div>
            <div className="example-prompts-list">
              {examples.map((ex) => (
                <button
                  key={ex}
                  className="example-chip"
                  onClick={() => setPrompt(ex)}
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>

          <div className="actions-row">
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                id="btn-generate"
                className="btn-generate"
                onClick={handleGenerate}
                disabled={status === 'loading' || !prompt.trim()}
              >
                {status === 'loading' ? (
                  <>
                    <span className="spinner-ring" style={{ width: 18, height: 18, borderWidth: 2 }} />
                    Generating…
                  </>
                ) : (
                  <>✦ Generate {activeTab === 'image' ? 'Image' : 'Video'}</>
                )}
              </button>
              {prompt && (
                <button className="btn-clear" onClick={() => setPrompt('')}>
                  Clear
                </button>
              )}
            </div>
            {prompt && (
              <button className="btn-action" onClick={handleCopyPrompt} title="Copy prompt">
                📋 Copy Prompt
              </button>
            )}
          </div>

          {status === 'loading' && (
            <div className="loading-container">
              <div className="spinner-ring" />
              <div className="loading-text">
                {activeTab === 'image' ? 'Generating your image…' : 'Generating your video…'}
              </div>
              <div className="loading-sub">This may take a few seconds</div>
            </div>
          )}

          {status === 'error' && error && (
            <div className="error-box">
              <span className="error-icon">⚠️</span>
              <div className="error-content">
                <div className="error-title">Generation Failed</div>
                <div className="error-msg">{error}</div>
              </div>
            </div>
          )}

          {status === 'success' && result && (
            <div className="result-section" ref={resultRef}>
              <div className="result-header">
                <div className="result-title">
                  Result
                  <span className="badge">Done</span>
                </div>
                <div className="result-actions">
                  <button id="btn-download" className="btn-action primary" onClick={handleDownload}>
                    ⬇ Download
                  </button>
                </div>
              </div>

              {result.type === 'image' ? (
                <div className="result-image-wrapper">
                  <img
                    id="result-image"
                    src={result.url}
                    alt="Generated image"
                    className="result-image"
                  />
                </div>
              ) : (
                <div className="result-video-wrapper">
                  <video
                    id="result-video"
                    src={result.url}
                    className="result-video"
                    controls
                    autoPlay
                    loop
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {history.length > 0 && (
          <section className="history-section">
            <div className="section-header">
              <div>
                <div className="section-title">Recent Generations</div>
                <div className="section-sub">{history.length} item{history.length !== 1 ? 's' : ''} — click to restore</div>
              </div>
              <button id="btn-clear-history" className="btn-clear-history" onClick={handleClearHistory}>
                Clear History
              </button>
            </div>

            <div className="history-grid">
              {history.map(item => (
                <div
                  key={item.id}
                  className="history-card"
                  onClick={() => handleHistoryClick(item)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && handleHistoryClick(item)}
                >
                  {item.type === 'image' ? (
                    <img
                      src={item.objectUrl}
                      alt={item.prompt}
                      className="history-card-media"
                    />
                  ) : (
                    <video
                      src={item.objectUrl}
                      className="history-card-media"
                      muted
                      playsInline
                    />
                  )}
                  <div className="history-card-body">
                    <div className="history-card-type">
                      {item.type === 'image' ? '🖼' : '🎬'} {item.type}
                    </div>
                    <div className="history-card-prompt">{item.prompt}</div>
                    <div className="history-card-time">
                      {new Date(item.createdAt).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {history.length === 0 && status === 'idle' && (
          <section className="history-section">
            <div className="empty-state">
              <div className="empty-icon">✦</div>
              <div className="empty-title">No generations yet</div>
              <div className="empty-sub">Your creations will appear here after you generate them.</div>
            </div>
          </section>
        )}
      </main>

      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast ${t.type}`}>
            {t.type === 'success' ? '✓' : '⚠'} {t.message}
          </div>
        ))}
      </div>
    </div>
  );
}
