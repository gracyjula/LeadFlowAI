import React, { useEffect, useState } from 'react';
import { auditApi } from '../api';

interface AuditEntry {
  id: string;
  lead_id: string;
  timestamp: string;
  event_type: string;
  input_data: any;
  enrichment_results: any;
  score: number | null;
  classification: string | null;
  classification_reason: string | null;
  approval_status: string | null;
  errors: string | null;
  details: any;
  draft_email: any;
  final_sent_email: any;
  tool_calls: any;
  actor: string | null;
}

const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [eventFilter, setEventFilter] = useState<string>('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    loadLogs();
  }, [eventFilter]);

  const loadLogs = async () => {
    try {
      const params: any = { limit: 100 };
      if (eventFilter) params.event_type = eventFilter;
      const res = await auditApi.list(params);
      setLogs(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const getEventBadge = (type: string) => {
    if (type.includes('ERROR') || type.includes('VIOLATION') || type.includes('REJECT')) return 'badge-rejected';
    if (type.includes('SENT') || type.includes('APPROVED') || type.includes('PASS')) return 'badge-approved';
    if (type.includes('CREATED') || type.includes('INGESTED') || type.includes('DRAFTED')) return 'badge-pending';
    if (type.includes('SCORED') || type.includes('CLASSIFIED') || type.includes('ROUTED') || type.includes('ENRICHED')) return 'badge-nurture';
    if (type.includes('INJECTION') || type.includes('FAIRNESS')) return 'badge-hot';
    return 'badge-pending';
  };

  const filteredLogs = searchTerm
    ? logs.filter(log =>
        log.event_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.lead_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (log.classification && log.classification.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    : logs;

  if (loading) return <div className="loading">Loading audit logs...</div>;

  return (
    <div>
      <h2>Audit Logs</h2>
      <p style={{ color: 'var(--text-light)', marginBottom: '1.5rem' }}>
        Complete audit trail of all lead processing events — traceability for every action
      </p>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>Filter Event:</span>
            <select value={eventFilter} onChange={e => setEventFilter(e.target.value)}
              style={{ padding: '0.375rem', borderRadius: '0.25rem', border: '1px solid var(--border)', marginLeft: '0.5rem' }}>
              <option value="">All Events</option>
              <option value="LEAD_CREATED">Lead Created</option>
              <option value="LEAD_INGESTED">Lead Ingested</option>
              <option value="LEAD_ENRICHED">Lead Enriched</option>
              <option value="LEAD_SCORED">Lead Scored</option>
              <option value="LEAD_CLASSIFIED">Lead Classified</option>
              <option value="LEAD_ROUTED">Lead Routed</option>
              <option value="EMAIL_DRAFTED">Email Drafted</option>
              <option value="EMAIL_APPROVE">Email Approved</option>
              <option value="EMAIL_REJECT">Email Rejected</option>
              <option value="EMAIL_EDIT">Email Edited</option>
              <option value="EMAIL_SENT">Email Sent</option>
              <option value="APPROVAL_PROCESSED">Approval Processed</option>
              <option value="FAIRNESS_TEST_RUN">Fairness Test</option>
              <option value="INJECTION_TEST_RUN">Injection Test</option>
              <option value="INJECTION_ATTEMPT_BLOCKED">Injection Blocked</option>
              <option value="PROCESSING_ERROR">Error</option>
            </select>
          </div>
          <div>
            <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>Search:</span>
            <input
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Search logs..."
              style={{ padding: '0.375rem', borderRadius: '0.25rem', border: '1px solid var(--border)', marginLeft: '0.5rem', width: '200px' }}
            />
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-light)' }}>
            {filteredLogs.length} of {logs.length} logs
          </span>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {filteredLogs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ color: 'var(--text-light)' }}>No audit logs found. Process leads to generate audit events.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event Type</th>
                  <th>Lead ID</th>
                  <th>Score</th>
                  <th>Classification</th>
                  <th>Actor</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map(entry => (
                  <React.Fragment key={entry.id}>
                    <tr onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
                      style={{ cursor: 'pointer' }}>
                      <td style={{ fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                      <td>
                        <span className={`badge ${getEventBadge(entry.event_type)}`}>
                          {entry.event_type}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
                        {entry.lead_id.substring(0, 8)}...
                      </td>
                      <td style={{ fontWeight: entry.score ? 600 : 400 }}>{entry.score ?? '-'}</td>
                      <td>
                        {entry.classification ? (
                          <span className={`badge ${entry.classification === 'HOT' ? 'badge-hot' : entry.classification === 'NURTURE' ? 'badge-nurture' : 'badge-disqualified'}`}>
                            {entry.classification}
                          </span>
                        ) : '-'}
                      </td>
                      <td style={{ fontSize: '0.75rem' }}>{entry.actor || 'system'}</td>
                      <td>
                        <button className="btn btn-outline" style={{ fontSize: '0.7rem', padding: '0.2rem 0.4rem' }}>
                          {expandedId === entry.id ? 'Collapse' : 'Expand'}
                        </button>
                      </td>
                    </tr>
                    {expandedId === entry.id && (
                      <tr>
                        <td colSpan={7} style={{ background: '#f8fafc', padding: '1rem' }}>
                          <div style={{ fontSize: '0.8rem', maxHeight: '400px', overflowY: 'auto' }}>
                            {entry.errors && (
                              <div style={{ color: 'var(--danger)', marginBottom: '0.5rem' }}>
                                <strong>Error:</strong> {entry.errors}
                              </div>
                            )}
                            {entry.input_data && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Input Data:</strong>
                                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '0.25rem', background: '#fff', padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border)' }}>
                                  {JSON.stringify(entry.input_data, null, 2)}
                                </pre>
                              </div>
                            )}
                            {entry.enrichment_results && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Enrichment Results:</strong>
                                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '0.25rem', background: '#fff', padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border)' }}>
                                  {JSON.stringify(entry.enrichment_results, null, 2)}
                                </pre>
                              </div>
                            )}
                            {entry.details && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Details:</strong>
                                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '0.25rem', background: '#fff', padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border)' }}>
                                  {JSON.stringify(entry.details, null, 2)}
                                </pre>
                              </div>
                            )}
                            {entry.draft_email && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Draft Email:</strong>
                                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '0.25rem', background: '#fff', padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border)' }}>
                                  {JSON.stringify(entry.draft_email, null, 2)}
                                </pre>
                              </div>
                            )}
                            {entry.final_sent_email && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Sent Email:</strong>
                                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '0.25rem', background: '#fff', padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border)' }}>
                                  {JSON.stringify(entry.final_sent_email, null, 2)}
                                </pre>
                              </div>
                            )}
                            {entry.tool_calls && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Tool Calls:</strong>
                                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '0.25rem', background: '#fff', padding: '0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border)' }}>
                                  {JSON.stringify(entry.tool_calls, null, 2)}
                                </pre>
                              </div>
                            )}
                            {entry.classification_reason && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Classification Reason:</strong>
                                <p style={{ marginTop: '0.25rem', whiteSpace: 'pre-wrap' }}>{entry.classification_reason}</p>
                              </div>
                            )}
                            {entry.approval_status && (
                              <div style={{ marginBottom: '0.5rem' }}>
                                <strong>Approval Status:</strong>
                                <span className={`badge ${entry.approval_status === 'APPROVED' || entry.approval_status === 'EDITED' ? 'badge-approved' : entry.approval_status === 'REJECTED' ? 'badge-rejected' : 'badge-pending'}`}
                                  style={{ marginLeft: '0.5rem' }}>
                                  {entry.approval_status}
                                </span>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditPage;