import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { FileUploader } from './components/upload/FileUploader';
import { ApprovalDashboard } from './components/admin/ApprovalDashboard';
import { Header } from './components/common/Header';
import { AuthProvider } from './contexts/AuthContext';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Header />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<FileUploader />} />
              <Route path="/admin" element={<ApprovalDashboard />} />
              <Route path="/upload/:customerId" element={<FileUploader />} />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
