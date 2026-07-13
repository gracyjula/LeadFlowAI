import React, { useEffect, useState } from 'react';
import { governanceApi, governanceApi as govApi, GovernanceStats } from '../api';
import { Page } from '../App';

interface Props {
  onNavigate: (page: Page, leadId?: string) => void;
}

const GovernancePage: React.FC<Props> = ({ onNavigate }) => {
  const [stats, setStats] = useState<GovernanceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const res = await governanceApi.stats();
      setStats(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load governance stats');
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    setRefreshing(true);
    await loadStats();
    setRefreshing(false);
  };

  if (loading) return <div className="loading">Loading governance data...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!stats) return <div className="loading">No governance data available</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2>Governance Dashboard</h2>
          <p style={{ color: 'var(--text-light)' }}>
            Audit, compliance, fairness, and security monitoring
          </p>
        </div>
        <button className="btn btn-outline" onClick={refresh} disabled={refreshing}>
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="grid">
        <div className="stat-card primary">
          <div className="value">{stats.total_audit_events}</div>
          <div className="label">Total Audit Events</div>
        </div>
        <div className="stat-card nurture">
          <div className="value">{stats.approval_requests}</div>
          <div className="label">Approval Requests</div>
        </div>
        <div className="stat-card success">
          <div className="value">{stats.approved_emails}</div>
          <div className="label">Approved Emails</div>
        </div>
        <div className="stat-card disqualified">
          <div className="value">{stats.rejected_emails}</div>
          <div className="label">Rejected Emails</div>
        </div>
        <div className="stat-card success">
          <div className="value">{stats.sent_emails}</div>
          <div className="label">Sent Emails</div>
        </div>
        <div className="stat-card hot">
          <div className="value">{stats.governance_violations}</div>
          <div className="label">Governance Violations</div>
        </div>
        <div className="stat-card primary">
          <div className="value">{stats.injection_attempts_blocked}</div>
          <div className="label">Injection Attempts Blocked</div>
        </div>
        <div className="stat-card success">
          <div className="value">{stats.fairness_tests_passed}/{stats.total_fairness_tests}</div>
          <div className="label">Fairness Tests Passed</div>
        </div>
        <div className="stat-card primary">
          <div className="value">{stats.total_injection_tests}</div>
          <div className="label">Injection Tests Run</div>
        </div>
      </div>

      <div className="two-column">
        <div className="card">
          <h2>Approval Pipeline</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span>Pending Approval</span>
                <span>{stats.approval_requests - stats.approved_emails - stats.rejected_emails}</span>
              </div>
              <div className="score-track">
                <div className="score-fill medium"
                  style={{ width: `${stats.approval_requests ? ((stats.approval_requests - stats.approved_emails - stats.rejected_emails) / stats.approval_requests) * 100 : 0}%` }} />
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span>Approved</span>
                <span>{stats.approved_emails}</span>
              </div>
              <div className="score-track">
                <div className="score-fill high"
                  style={{ width: `${stats.approval_requests ? (stats.approved_emails / stats.approval_requests) * 100 : 0}%` }} />
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span>Rejected</span>
                <span>{stats.rejected_emails}</span>
              </div>
              <div className="score-track">
                <div className="score-fill low"
                  style={{ width: `${stats.approval_requests ? (stats.rejected_emails / stats.approval_requests) * 100 : 0}%` }} />
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h2>Security & Compliance</h2>
          <table>
            <tbody>
              <tr>
                <td><strong>Injection Attempts</strong></td>
                <td>
                  <span className={`badge ${stats.injection_attempts_blocked > 0 ? 'badge-approved' : 'badge-pending'}`}>
                    {stats.injection_attempts_blocked > 0 ? 'Blocked' : 'None'}
                  </span>
                </td>
              </tr>
              <tr>
                <td><strong>Fairness Status</strong></td>
                <td>
                  <span className={`badge ${stats.fairness_tests_passed === stats.total_fairness_tests && stats.total_fairness_tests > 0 ? 'badge-approved' : stats.total_fairness_tests > 0 ? 'badge-rejected' : 'badge-pending'}`}>
                    {stats.total_fairness_tests > 0 ? (stats.fairness_tests_passed === stats.total_fairness_tests ? 'All Passed' : 'Issues Found') : 'Not Tested'}
                  </span>
                </td>
              </tr>
              <tr>
                <td><strong>Governance Violations</strong></td>
                <td>
                  <span className={`badge ${stats.governance_violations > 0 ? 'badge-rejected' : 'badge-approved'}`}>
                    {stats.governance_violations > 0 ? `${stats.governance_violations} Found` : 'None'}
                  </span>
                </td>
              </tr>
              <tr>
                <td><strong>Sent Emails (Approved)</strong></td>
                <td><span className="badge badge-approved">{stats.sent_emails}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h2>Governance Actions</h2>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => onNavigate('audit')}>
            View Audit Logs
          </button>
          <button className="btn btn-outline" onClick={() => onNavigate('tests')}>
            Run Tests
          </button>
          <button className="btn btn-outline" onClick={() => onNavigate('leads')}>
            Review Leads
          </button>
        </div>
      </div>
    </div>
  );
};

export default GovernancePage;