import React, { useEffect, useState } from 'react';
import { leadApi, LeadResponse } from '../api';
import { Page } from '../App';

interface Props {
  onNavigate: (page: Page, leadId?: string) => void;
}

const LeadsPage: React.FC<Props> = ({ onNavigate }) => {
  const [leads, setLeads] = useState<LeadResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('');

  useEffect(() => {
    loadLeads();
  }, [filter]);

  const loadLeads = async () => {
    try {
      const params: any = { limit: 100 };
      if (filter) params.classification = filter;
      const res = await leadApi.list(params);
      setLeads(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load leads');
    } finally {
      setLoading(false);
    }
  };

  const getBadgeClass = (classification: string | null) => {
    switch (classification) {
      case 'HOT': return 'badge-hot';
      case 'NURTURE': return 'badge-nurture';
      case 'DISQUALIFY': return 'badge-disqualified';
      default: return 'badge-pending';
    }
  };

  const getScoreClass = (score: number | null) => {
    if (!score) return 'low';
    if (score >= 80) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  };

  if (loading) return <div className="loading">Loading leads...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>Leads</h2>
        <button className="btn btn-primary" onClick={() => onNavigate('new-lead')}>
          + New Lead
        </button>
      </div>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>Filter:</span>
          <select value={filter} onChange={e => setFilter(e.target.value)} style={{ padding: '0.375rem', borderRadius: '0.25rem', border: '1px solid var(--border)' }}>
            <option value="">All Leads</option>
            <option value="HOT">HOT</option>
            <option value="NURTURE">NURTURE</option>
            <option value="DISQUALIFY">DISQUALIFIED</option>
          </select>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {leads.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ color: 'var(--text-light)' }}>No leads found. Create your first lead to get started.</p>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => onNavigate('new-lead')}>
            Create Lead
          </button>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Company</th>
                  <th>Job Title</th>
                  <th>Score</th>
                  <th>Classification</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {leads.map(lead => (
                  <tr key={lead.id} onClick={() => onNavigate('lead-detail', lead.id)} style={{ cursor: 'pointer' }}>
                    <td><strong>{lead.name}</strong></td>
                    <td>{lead.company_name || '-'}</td>
                    <td>{lead.job_title || '-'}</td>
                    <td>
                      <div className="score-bar">
                        <span style={{ fontWeight: 600 }}>{lead.score ?? '-'}</span>
                        <div className="score-track">
                          <div className={`score-fill ${getScoreClass(lead.score)}`} style={{ width: `${lead.score || 0}%` }} />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${getBadgeClass(lead.classification)}`}>
                        {lead.classification || 'PENDING'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.75rem' }}>{lead.status}</td>
                    <td>
                      <button className="btn btn-outline" style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                        onClick={(e) => { e.stopPropagation(); onNavigate('lead-detail', lead.id); }}>
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default LeadsPage;