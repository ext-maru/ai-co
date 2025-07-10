import { useState } from 'react';
import FourSagesIntegration from './components/FourSagesIntegration';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import './App.css'

function App() {
  const [activeView, setActiveView] = useState<'sages' | 'analytics'>('sages');

  return (
    <div className="App">
      <nav className="app-nav">
        <h1>AI Company Dashboard</h1>
        <div className="nav-buttons">
          <button
            className={activeView === 'sages' ? 'active' : ''}
            onClick={() => setActiveView('sages')}
          >
            4賢者システム
          </button>
          <button
            className={activeView === 'analytics' ? 'active' : ''}
            onClick={() => setActiveView('analytics')}
          >
            高度分析
          </button>
        </div>
      </nav>

      <main className="app-content">
        {activeView === 'sages' ? (
          <FourSagesIntegration />
        ) : (
          <AnalyticsDashboard />
        )}
      </main>
    </div>
  );
}

export default App
