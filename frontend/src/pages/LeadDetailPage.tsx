import React, { useEffect, useState } from 'react';
import { leadApi, LeadDetailResponse, ApprovalRequest } from '../api';
import { Page } from '../App';

interface Props {
  leadId: string;
  onNavigate: (page: Page, leadId?: string) => void;
}

const LeadDetailPage: React.FC<Props> = ({ leadId, onNavigate }) => {
  const [lead, setLead] = useState<LeadDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<string>('');
  const [comment, setComment] = useState('');
  const [editSubject, setEditSubject] = useState('');
  const [editBody, setEditBody] = useState('');
  const [showEdit, setShowEdit] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    loadLead();
  }, [leadId]);

  const loadLead = async () => {
    try {
      const res = await leadApi.get(leadId);
      setLead(res.data);
      if (res.data.draft_email_body) {
        setEditSubject(res.data.edited_email_subject || res.data.draft_email_subject || '');
        setEditBody(res.data.edited_email_body || res.data.draft_email_body || '');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load lead');
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (approvalAction: string) => {
    setProcessing(true);
    setMessage(null);
    try {
      const data: ApprovalRequest = {
        action: approvalAction as 'approve' | 'reject' | 'edit',
        comment: comment || undefined,
      };
      if (approvalAction === 'edit' || approvalAction === 'approve') {
        if (editSubject) data.edited_email_subject = editSubject;
        if (editBody) data.edited_email_body = editBody;
      }
      const res = await leadApi.approve(leadId, data);
      setMessage(res.data.message);
      loadLead();
    } catch (err: any) {
      setMessage(`Error: ${err.response?.data?.detail || 'Failed to process approval'}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleSend = async () => {
    setProcessing(true);
    setMessage(null);
    try {
      const res = await leadApi.send(leadId);
      setMessage(res.data.message);
      loadLead();
    } catch (err: any) {
      setMessage(`Error: ${err.response?.data?.detail || 'Failed to send email'}`);
    } finally {
      setProcessing(false);
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

  const getApprovalBadge = (status: string) => {
    switch (status) {
      case 'APPROVED': return 'badge-approved';
      case 'EDITED': return 'badge-approved';
      case 'REJECTED': return 'badge-rejected';
      case 'PENDING': return 'badge-pending';
      default: return 'badge-pending';
    }
  };

  if (loading) return <div className="loading">Loading lead details...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!lead) return <div className="error">Lead not found</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <button className="btn btn-outline" onClick={() => onNavigate('leads')} style={{ marginRight: '1rem' }}>
            ← Back
          </button>
          <h2 style={{ display: 'inline' }}>{lead.name}</h2>
        </div>
        <span className={`badge ${getBadgeClass(lead.classification)}`} style={{ fontSize: '1rem', padding: '0.5rem 1.5rem' }}>
          {lead.classification || 'PENDING'}
        </span>
      </div>

      {message && (
        <div className={message.includes('Error') ? 'error' : 'success'}>{message}</div>
      )}

      <div className="two-column">
        <div>
          <div className="card">
            <h3>Lead Information</h3>
            <table>
              <tbody>
                <tr><td><strong>Email</strong></td><td>{lead.email}</td></tr>
                <tr><td><strong>Job Title</strong></td><td>{lead.job_title || '-'}</td></tr>
                <tr><td><strong>Company</strong></td><td>{lead.company_name || '-'}</td></tr>
                <tr><td><strong>Website</strong></td><td>{lead.company_website || '-'}</td></tr>
                <tr><td><strong>Company Size</strong></td><td>{lead.company_size || '-'}</td></tr>
                <tr><td><strong>Industry</strong></td><td>{lead.industry || '-'}</td></tr>
                <tr><td><strong>Status</strong></td><td>{lead.status}</td></tr>
              </tbody>
            </table>
          </div>

          <div className="card">
            <h3>Enrichment Results</h3>
            <table>
              <tbody>
                <tr><td><strong>Industry</strong></td><td>{lead.enriched_industry || '-'}</td></tr>
                <tr><td><strong>Company Size</strong></td><td>{lead.enriched_company_size || '-'}</td></tr>
                <tr><td><strong>Revenue</strong></td><td>{lead.estimated_revenue || '-'}</td></tr>
                <tr><td><strong>Market Segment</strong></td><td>{lead.market_segment || '-'}</td></tr>
                <tr><td><strong>Decision Maker</strong></td><td>{lead.decision_maker_status ? 'Yes' : 'No'}</td></tr>
                <tr><td><strong>Buying Signals</strong></td><td>{lead.buying_signals ? (Array.isArray(lead.buying_signals) ? lead.buying_signals.join(', ') : lead.buying_signals) : '-'}</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <div className="card">
            <h3>Score: {lead.score}/100</h3>
            <div className="score-bar" style={{ marginBottom: '1rem' }}>
              <div className="score-track" style={{ height: '12px' }}>
                <div className={`score-fill ${(lead.score || 0) >= 80 ? 'high' : (lead.score || 0) >= 40 ? 'medium' : 'low'}`}
                  style={{ width: `${lead.score || 0}%` }} />
              </div>
            </div>
            <table>
              <tbody>
                <tr><td><strong>Industry</strong></td><td>{lead.industry_score}/25</td></tr>
                <tr><td><strong>Company Size</strong></td><td>{lead.company_size_score}/20</td></tr>
                <tr><td><strong>Role</strong></td><td>{lead.role_score}/25</td></tr>
                <tr><td><strong>Buying Intent</strong></td><td>{lead.buying_intent_score}/30</td></tr>
              </tbody>
            </table>
            {lead.score_reason && (
              <div style={{ marginTop: '1rem' }}>
                <strong>Rationale:</strong>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8rem', marginTop: '0.5rem', background: '#f8fafc', padding: '0.75rem', borderRadius: '0.375rem' }}>
                  {lead.score_reason}
                </pre>
              </div>
            )}
          </div>

          {lead.message && (
            <div className="card">
              <h3>Lead Message</h3>
              <p style={{ fontSize: '0.875rem', background: '#f8fafc', padding: '0.75rem', borderRadius: '0.375rem' }}>{lead.message}</p>
            </div>
          )}
        </div>
      </div>

      {lead.draft_email_body && (
        <div className="card">
          <h3>Email Draft</h3>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span className={`badge ${getApprovalBadge(lead.approval_status)}`}>{lead.approval_status}</span>
            <span className="badge badge-pending">{lead.email_status}</span>
          </div>

          <div className="email-preview">
            <div className="subject">{lead.edited_email_subject || lead.draft_email_subject}</div>
            <div>{lead.edited_email_body || lead.draft_email_body}</div>
          </div>

          {lead.sent_email_body && (
            <div className="email-preview" style={{ borderColor: 'var(--success)' }}>
              <div className="subject" style={{ color: 'var(--success)' }}>✓ Sent: {lead.sent_email_subject}</div>
              <div>{lead.sent_email_body}</div>
              <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-light)' }}>
                Sent at: {lead.sent_at ? new Date(lead.sent_at).toLocaleString() : 'N/A'}
              </div>
            </div>
          )}

          {lead.classification === 'HOT' && lead.approval_status === 'PENDING' && (
            <div style={{ marginTop: '1rem' }}>
              <h3>Approval Actions</h3>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <button className="btn btn-success" onClick={() => handleApproval('approve')} disabled={processing}>
                  Approve
                </button>
                <button className="btn btn-warning" onClick={() => setShowEdit(!showEdit)} disabled={processing}>
                  Edit & Approve
                </button>
                <button className="btn btn-danger" onClick={() => handleApproval('reject')} disabled={processing}>
                  Reject
                </button>
              </div>

              <div className="form-group">
                <label>Comment (optional)</label>
                <input value={comment} onChange={e => setComment(e.target.value)} placeholder="Add a comment..." />
              </div>

              {showEdit && (
                <div>
                  <div className="form-group">
                    <label>Edited Subject</label>
                    <input value={editSubject} onChange={e => setEditSubject(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label>Edited Body</label>
                    <textarea value={editBody} onChange={e => setEditBody(e.target.value)} rows={8} />
                  </div>
                  <button className="btn btn-success" onClick={() => handleApproval('edit')} disabled={processing}>
                    Save Edits & Approve
                  </button>
                </div>
              )}
            </div>
          )}

          {(lead.approval_status === 'APPROVED' || lead.approval_status === 'EDITED') && lead.status !== 'SENT' && (
            <div style={{ marginTop: '1rem' }}>
              <button className="btn btn-success" onClick={handleSend} disabled={processing}>
                Send Email Now
              </button>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-light)', marginTop: '0.25rem' }}>
                Email will be sent to {lead.email}
              </p>
            </div>
          )}

          {lead.approval_comment && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--text-light)' }}>
              <strong>Reviewer Comment:</strong> {lead.approval_comment}
            </div>
          )}
        </div>
      )}

      {lead.routing_action && (
        <div className="card">
          <h3>Routing</h3>
          <p><strong>Action:</strong> {lead.routing_action}</p>
          {lead.routing_reason && <p style={{ fontSize: '0.875rem' }}>{lead.routing_reason}</p>}
        </div>
      )}
    </div>
  );
};

export default LeadDetailPage;