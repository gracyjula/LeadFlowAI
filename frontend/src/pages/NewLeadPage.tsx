import React, { useState } from 'react';
import { leadApi, LeadCreate, ProcessResponse } from '../api';
import { Page } from '../App';

interface Props {
  onNavigate: (page: Page, leadId?: string) => void;
}

const NewLeadPage: React.FC<Props> = ({ onNavigate }) => {
  const [form, setForm] = useState<LeadCreate>({
    name: '',
    email: '',
    job_title: '',
    company_name: '',
    company_website: '',
    company_size: '',
    industry: '',
    message: '',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await leadApi.process(form);
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process lead');
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

  return (
    <div className="two-column">
      <div>
        <h2>New Lead</h2>
        <p style={{ color: 'var(--text-light)', marginBottom: '1.5rem' }}>
          Enter lead information for AI-powered qualification
        </p>

        <div className="card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Name *</label>
              <input name="name" value={form.name} onChange={handleChange} required placeholder="John Smith" />
            </div>

            <div className="form-group">
              <label>Email *</label>
              <input name="email" type="email" value={form.email} onChange={handleChange} required placeholder="john@company.com" />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Job Title</label>
                <input name="job_title" value={form.job_title} onChange={handleChange} placeholder="CTO" />
              </div>
              <div className="form-group">
                <label>Company Name</label>
                <input name="company_name" value={form.company_name} onChange={handleChange} placeholder="TechCorp Inc" />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Company Website</label>
                <input name="company_website" value={form.company_website} onChange={handleChange} placeholder="https://techcorp.com" />
              </div>
              <div className="form-group">
                <label>Company Size</label>
                <input name="company_size" value={form.company_size} onChange={handleChange} placeholder="500" />
              </div>
            </div>

            <div className="form-group">
              <label>Industry</label>
              <select name="industry" value={form.industry} onChange={handleChange}>
                <option value="">Select industry...</option>
                <option value="SaaS">SaaS</option>
                <option value="Technology">Technology</option>
                <option value="Finance">Finance</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Education">Education</option>
                <option value="Manufacturing">Manufacturing</option>
                <option value="Retail">Retail</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label>Message / Inquiry</label>
              <textarea name="message" value={form.message} onChange={handleChange} placeholder="We are evaluating new solutions and would like to see a demo..." rows={4} />
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
              {loading ? 'Processing...' : 'Submit & Process Lead'}
            </button>
          </form>
        </div>
      </div>

      <div>
        <h2>Result</h2>
        <p style={{ color: 'var(--text-light)', marginBottom: '1.5rem' }}>
          AI analysis will appear here after submission
        </p>

        {error && <div className="error">{error}</div>}

        {result && (
          <div>
            <div className="card">
              <h3>Classification</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                <span className={`badge ${getBadgeClass(result.classification)}`} style={{ fontSize: '1rem', padding: '0.5rem 1.5rem' }}>
                  {result.classification || 'PENDING'}
                </span>
                <span style={{ fontSize: '1.5rem', fontWeight: 700 }}>{result.score}/100</span>
              </div>

              <h3>Score Breakdown</h3>
              <div className="score-bar" style={{ marginBottom: '1rem' }}>
                <div className="score-track" style={{ height: '12px' }}>
                  <div className={`score-fill ${(result.score || 0) >= 80 ? 'high' : (result.score || 0) >= 40 ? 'medium' : 'low'}`}
                    style={{ width: `${result.score || 0}%` }} />
                </div>
              </div>

              {result.score_reason && (
                <div>
                  <h3>Scoring Rationale</h3>
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.875rem', background: '#f8fafc', padding: '1rem', borderRadius: '0.375rem', border: '1px solid var(--border)' }}>
                    {result.score_reason}
                  </pre>
                </div>
              )}

              {result.classification_reason && (
                <div style={{ marginTop: '1rem' }}>
                  <h3>Classification Reason</h3>
                  <p style={{ fontSize: '0.875rem' }}>{result.classification_reason}</p>
                </div>
              )}

              {result.routing_action && (
                <div style={{ marginTop: '1rem' }}>
                  <h3>Routing</h3>
                  <p style={{ fontSize: '0.875rem' }}><strong>Action:</strong> {result.routing_action}</p>
                </div>
              )}
            </div>

            {result.draft_email_body && (
              <div className="card">
                <h3>Draft Email</h3>
                <div className="email-preview">
                  <div className="subject">{result.draft_email_subject}</div>
                  <div>{result.draft_email_body}</div>
                </div>
                <div style={{ marginTop: '0.5rem' }}>
                  <span className="badge badge-pending">PENDING APPROVAL</span>
                  <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: 'var(--text-light)' }}>
                    Email will not be sent until approved
                  </span>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
              <button className="btn btn-outline" onClick={() => onNavigate('lead-detail', result.lead_id)}>
                View Full Details
              </button>
              <button className="btn btn-outline" onClick={() => {
                setForm({ name: '', email: '', job_title: '', company_name: '', company_website: '', company_size: '', industry: '', message: '' });
                setResult(null);
                setError(null);
              }}>
                Clear & New
              </button>
            </div>
          </div>
        )}

        {!result && !error && (
          <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-light)' }}>
            <p>Submit a lead to see AI-powered qualification results including scoring, classification, routing, and email draft.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default NewLeadPage;