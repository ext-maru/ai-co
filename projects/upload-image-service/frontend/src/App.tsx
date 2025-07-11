import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ContractUploadFlow } from './components/contract/ContractUploadFlow';
import { SimpleContractReview } from './components/admin/SimpleContractReview';
import { SubmissionDashboard } from './components/admin/SubmissionDashboard';
import { SubmissionPage } from './components/submission/SubmissionPage';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<ContractUploadFlow />} />
          <Route path="/admin" element={<SubmissionDashboard />} />
          <Route path="/admin/old" element={<SimpleContractReview />} />
          <Route path="/contract/:contractId" element={<ContractUploadFlow />} />
          <Route path="/submit/:urlKey" element={<SubmissionPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
