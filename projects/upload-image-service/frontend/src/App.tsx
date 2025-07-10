import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ContractUploadFlow } from './components/contract/ContractUploadFlow';
import { SimpleContractReview } from './components/admin/SimpleContractReview';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<ContractUploadFlow />} />
          <Route path="/admin" element={<SimpleContractReview />} />
          <Route path="/contract/:contractId" element={<ContractUploadFlow />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
