export default function Home() {
  return (
    <main style={{ padding: 'var(--space-8)', maxWidth: '1200px', margin: '0 auto' }}>
      <div className="glass-card" style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
        <h1 style={{ fontSize: 'var(--font-4xl)', color: 'var(--text-primary)', marginBottom: 'var(--space-4)' }}>
          Arena<span style={{ color: 'var(--accent-primary)' }}>X</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-lg)', marginBottom: 'var(--space-6)' }}>
          Open-Source LLM Battleground & Evaluation Platform
        </p>
        <div style={{ display: 'inline-flex', gap: 'var(--space-4)', padding: 'var(--space-3) var(--space-6)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-full)', border: '1px solid var(--border-medium)' }}>
          <span style={{ color: 'var(--accent-cyan)' }}>Sub-phase 1.1 Active</span>
          <span style={{ color: 'var(--text-muted)' }}>|</span>
          <span style={{ color: 'var(--status-success)' }}>Workspace Configured</span>
        </div>
      </div>
    </main>
  );
}
