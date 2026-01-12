import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getHistoryConversation } from '../api/client';
import type { ConversationDetail } from '../api/client';
import { ConversationBubble } from '../components/ConversationBubble';
import { ScoreCard } from '../components/ScoreCard';

export function HistoryConversationViewer() {
  const { id } = useParams<{ id: string }>();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'transcript' | 'understanding' | 'ideation' | 'rollout' | 'judgment'>('transcript');

  const fetchConversation = useCallback(async () => {
    if (!id) return;
    
    try {
      setError(null);
      setLoading(true);
      const res = await getHistoryConversation(decodeURIComponent(id));
      setConversation(res.data);
    } catch (err) {
      setError('Failed to load conversation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchConversation();
  }, [fetchConversation]);

  if (loading) {
    return <div className="page loading">Loading conversation...</div>;
  }

  if (error || !conversation) {
    return (
      <div className="page">
        <div className="error-banner">{error || 'Conversation not found'}</div>
        <Link to="/history" className="back-link">← Back to History</Link>
      </div>
    );
  }

  // Parse run_id from the conversation id
  const runId = id?.split(':')[0] || 'unknown';

  return (
    <div className="page conversation-viewer">
      <div className="page-header">
        <Link to={`/history?run=${runId}`} className="back-link">← Back to {runId === 'default' ? 'Default Results' : `Run ${runId}`}</Link>
        <h1>{conversation.behavior}</h1>
        <span className="muted">{conversation.turn_count} turns • Run: {runId}</span>
      </div>

      {/* Score Card */}
      {conversation.judgment && (
        <ScoreCard judgment={conversation.judgment} />
      )}

      {/* Tabs */}
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'transcript' ? 'active' : ''}`}
          onClick={() => setActiveTab('transcript')}
        >
          💬 Transcript
        </button>
        <button 
          className={`tab ${activeTab === 'understanding' ? 'active' : ''}`}
          onClick={() => setActiveTab('understanding')}
          disabled={!conversation.understanding}
        >
          🧠 Understanding
        </button>
        <button 
          className={`tab ${activeTab === 'ideation' ? 'active' : ''}`}
          onClick={() => setActiveTab('ideation')}
          disabled={!conversation.ideation}
        >
          💡 Ideation
        </button>
        <button 
          className={`tab ${activeTab === 'rollout' ? 'active' : ''}`}
          onClick={() => setActiveTab('rollout')}
          disabled={!conversation.rollout}
        >
          🎭 Rollout
        </button>
        <button 
          className={`tab ${activeTab === 'judgment' ? 'active' : ''}`}
          onClick={() => setActiveTab('judgment')}
          disabled={!conversation.judgment}
        >
          ⚖️ Judgment
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'transcript' && (
          <div className="transcript-view">
            {conversation.transcript && conversation.transcript.length > 0 ? (
              conversation.transcript.map((msg, idx) => (
                <ConversationBubble key={idx} message={msg} />
              ))
            ) : (
              <p className="muted">No transcript available</p>
            )}
          </div>
        )}

        {activeTab === 'understanding' && conversation.understanding && (
          <div className="stage-view">
            <pre className="json-view">
              {JSON.stringify(conversation.understanding, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === 'ideation' && conversation.ideation && (
          <div className="stage-view">
            <h4>Generated Variations</h4>
            {conversation.ideation.evals && conversation.ideation.evals.map((evalItem: any, idx: number) => (
              <div key={idx} className="variation-card">
                <strong>Variation {idx + 1}</strong>
                <p>{evalItem.variation_description}</p>
              </div>
            ))}
            <details>
              <summary>Raw JSON</summary>
              <pre className="json-view">
                {JSON.stringify(conversation.ideation, null, 2)}
              </pre>
            </details>
          </div>
        )}

        {activeTab === 'rollout' && conversation.rollout && (
          <div className="stage-view">
            {conversation.rollout.rollouts && conversation.rollout.rollouts.map((rolloutItem: any, idx: number) => (
              <div key={idx} className="rollout-card">
                <h4>Rollout {idx + 1}</h4>
                <p><strong>Description:</strong> {rolloutItem.variation_description}</p>
                {rolloutItem.elicitation_detected !== undefined && (
                  <p><strong>Elicitation Detected:</strong> {rolloutItem.elicitation_detected ? 'Yes' : 'No'}</p>
                )}
              </div>
            ))}
            <details>
              <summary>Raw JSON</summary>
              <pre className="json-view">
                {JSON.stringify(conversation.rollout, null, 2)}
              </pre>
            </details>
          </div>
        )}

        {activeTab === 'judgment' && conversation.judgment && (
          <div className="stage-view">
            <div className="judgment-summary">
              {conversation.judgment.summary_statistics && (
                <>
                  <div className="judgment-stat">
                    <span className="label">Avg Behavior Presence:</span>
                    <span className="value">
                      {conversation.judgment.summary_statistics.average_behavior_presence_score?.toFixed(2) || 'N/A'}
                    </span>
                  </div>
                  <div className="judgment-stat">
                    <span className="label">Max Behavior Presence:</span>
                    <span className="value">
                      {conversation.judgment.summary_statistics.max_behavior_presence_score?.toFixed(2) || 'N/A'}
                    </span>
                  </div>
                </>
              )}
            </div>
            
            {conversation.judgment.judgments && conversation.judgment.judgments.map((j: any, idx: number) => (
              <div key={idx} className="judgment-card">
                <h4>Judgment {idx + 1}</h4>
                <p><strong>Score:</strong> {j.behavior_presence_score}</p>
                {j.reasoning && (
                  <div className="reasoning">
                    <strong>Reasoning:</strong>
                    <p>{j.reasoning}</p>
                  </div>
                )}
              </div>
            ))}
            
            <details>
              <summary>Raw JSON</summary>
              <pre className="json-view">
                {JSON.stringify(conversation.judgment, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );
}

