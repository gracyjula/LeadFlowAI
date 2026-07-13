import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import GovernancePage from './pages/GovernancePage';
import EvaluationPage from './pages/EvaluationPage';
import LeadsPage from './pages/LeadsPage';
import LeadDetailPage from './pages/LeadDetailPage';
import NewLeadPage from './pages/NewLeadPage';
import TestsPage from './pages/TestsPage';
import AuditPage from './pages/AuditPage';

export type Page = 'dashboard' | 'governance' | 'evaluation' | 'leads' | 'lead-detail' | 'new-lead' | 'tests' | 'audit';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);

  const navigate = (page: Page, leadId?: string) => {
    if (leadId) setSelectedLeadId(leadId);
    setCurrentPage(page);
  };

  return (
    <div className="app">
      <nav className="navbar">
        <div>
          <h1>LeadFlowAI</h1>
          <span className="subtitle">Lead Qualification & Outreach Agent</span>
        </div>
        <div className="nav-tabs">
          <button className={`nav-tab ${currentPage === 'dashboard' ? 'active' : ''}`} onClick={() => navigate('dashboard')}>Dashboard</button>
          <button className={`nav-tab ${currentPage === 'governance' ? 'active' : ''}`} onClick={() => navigate('governance')}>Governance</button>
          <button className={`nav-tab ${currentPage === 'evaluation' ? 'active' : ''}`} onClick={() => navigate('evaluation')}>Evaluation</button>
          <button className={`nav-tab ${currentPage === 'leads' ? 'active' : ''}`} onClick={() => navigate('leads')}>Leads</button>
          <button className={`nav-tab ${currentPage === 'new-lead' ? 'active' : ''}`} onClick={() => navigate('new-lead')}>New Lead</button>
          <button className={`nav-tab ${currentPage === 'tests' ? 'active' : ''}`} onClick={() => navigate('tests')}>Tests</button>
          <button className={`nav-tab ${currentPage === 'audit' ? 'active' : ''}`} onClick={() => navigate('audit')}>Audit</button>
        </div>
      </nav>

      <div className="container">
        {currentPage === 'dashboard' && <Dashboard onNavigate={navigate} />}
        {currentPage === 'governance' && <GovernancePage onNavigate={navigate} />}
        {currentPage === 'evaluation' && <EvaluationPage onNavigate={navigate} />}
        {currentPage === 'leads' && <LeadsPage onNavigate={navigate} />}
        {currentPage === 'lead-detail' && selectedLeadId && <LeadDetailPage leadId={selectedLeadId} onNavigate={navigate} />}
        {currentPage === 'new-lead' && <NewLeadPage onNavigate={navigate} />}
        {currentPage === 'tests' && <TestsPage />}
        {currentPage === 'audit' && <AuditPage />}
      </div>
    </div>
  );
}

export default App;