import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AdminPage from './components/AdminPage';
import SubmissionPage from './components/SubmissionPage';
import SettingsPage from './components/SettingsPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/submission/:sessionId" element={<SubmissionPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/" element={<AdminPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
