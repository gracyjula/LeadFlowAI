import React, { useEffect, useState } from 'react';
import { dashboardApi, DashboardStats, testApi } from '../api';
import { Page } from '../App';

interface Props {
  onNavigate: (page: Page, leadId?: string) => void;
}

const Dashboard: React.FC<Props> = ({ onNavigate }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fairnessResult, setFairnessResult] = useState<any>(null);
  const [injectionResult, setInjectionResult] = useState<any>(null);

  useEffect(() => {
    loadStats();
    loadTestResults();
  }, []);

  const loadStats = async () => {
    try {
      const res = await dashboardApi.stats();
      setStats(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadTestResults = async () => {
    try {
      const [fairness, injection] = await Promise.all([
        testApi.getFairness(),
        testApi.getInjection(),
      ]);
      // Only set if the response contains actual data (not a "no tests run" message)
      if (fairness.data && fairness.data.test_passed !== null && fairness.data.test_passed !== undefined) {
        setFairnessResult(fairness.data);
      }
      if (injection.data && injection.data.test_passed !== null && injection.data.test_passed !== undefined) {
        setInjectionResult(injection.data);
      }
    } catch {
      // Test results may not exist yet — silently ignore
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!stats) return <div className="loading">No data available</div>;

  const hasTestResults = fairnessResult !== null || injectionResult !== null;

  return (
    <div>
      <h2>Dashboard</h2>
      <p style={{ color: 'var(--text-light)', marginBottom: '1.5rem' }}>
        Real-time overview of lead qualification pipeline
      </p>

      <div className="grid">
        <div className="stat-card primary">
          <div className="value">{stats.total_leads}</div>
          <div className="label">Total Leads</div>
        </div>
        <div className="stat-card hot">
          <div className="value">{stats.hot_leads}</div>
          <div className="label">HOT</div>
        </div>
        <div className="stat-card nurture">
          <div className="value">{stats.nurture_leads}</div>
          <div className="label">NURTURE</div>
        </div>
        <div className="stat-card disqualified">
          <div className="value">{stats.disqualified_leads}</div>
          <div className="label">DISQUALIFIED</div>
        </div>
        <div className="stat-card primary">
          <div className="value">{stats.average_score}</div>
          <div className="label">Avg Score</div>
        </div>
        <div className="stat-card success">
          <div className="value">{stats.approval_rate}%</div>
          <div className="label">Approval Rate</div>
        </div>
        <div className="stat-card primary">
          <div className="value">{stats.email_draft_count}</div>
          <div className="label">Email Drafts</div>
        </div>
        <div className="stat-card success">
          <div className="value">{stats.sent_count}</div>
          <div className="label">Sent</div>
        </div>
      </div>

      <div className="two-column">
        <div className="card">
          <h2>Quick Actions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <button className="btn btn-primary" onClick={() => onNavigate('new-lead')}>
              + New Lead
            </button>
            <button className="btn btn-outline" onClick={() => onNavigate('leads')}>
              View All Leads
            </button>
            <button className="btn btn-outline" onClick={() => onNavigate('tests')}>
              Run Tests
            </button>
          </div>
        </div>

        <div className="card">
          <h2>Pipeline Status</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span>HOT (SDR Queue)</span>
                <span>{stats.hot_leads}</span>
              </div>
              <div className="score-track">
                <div className="score-fill high" style={{ width: `${stats.total_leads ? (stats.hot_leads / stats.total_leads) * 100 : 0}%` }} />
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span>NURTURE</span>
                <span>{stats.nurture_leads}</span>
              </div>
              <div className="score-track">
                <div className="score-fill medium" style={{ width: `${stats.total_leads ? (stats.nurture_leads / stats.total_leads) * 100 : 0}%` }} />
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span>Pending Approval</span>
                <span>{stats.pending_approval_count}</span>
              </div>
              <div className="score-track">
                <div className="score-fill medium" style={{ width: `${stats.total_leads ? (stats.pending_approval_count / stats.total_leads) * 100 : 0}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {hasTestResults && (
        <div className="card">
          <h2>Latest Test Results</h2>
          <div className="two-column">
            {fairnessResult && (
              <div className={`test-result ${fairnessResult.test_passed ? 'pass' : 'fail'}`}>
                <strong>Fairness Test:</strong> {fairnessResult.test_passed ? 'PASSED' : 'FAILED'}
                <br />
                <small>Lead A: {fairnessResult.lead_a_name} (Score: {fairnessResult.score_a})</small>
                <br />
                <small>Lead B: {fairnessResult.lead_b_name} (Score: {fairnessResult.score_b})</small>
              </div>
            )}
            {injectionResult && (
              <div className={`test-result ${injectionResult.test_passed ? 'pass' : 'fail'}`}>
                <strong>Injection Test:</strong> {injectionResult.test_passed ? 'PASSED' : 'FAILED'}
                <br />
                <small>Score: {injectionResult.score_returned}</small>
                <br />
                <small>Classification: {injectionResult.classification_returned}</small>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;