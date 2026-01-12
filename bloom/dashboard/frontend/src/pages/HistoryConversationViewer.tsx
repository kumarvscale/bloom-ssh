import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getHistoryConversation } from '../api/client';
import type { ConversationDetail } from '../api/client';
import { ConversationBubble } from '../components/ConversationBubble';
import { ScoreCard } from '../components/ScoreCard';

// Helper to check if judgment is assistant harmfulness type
function isHarmfulnessJudgment(judgment: any): boolean {
  return judgment?.judgment_type === 'assistant_harmfulness';
}

// Helper to parse XML-style content into array of items
function parseXmlContent(content: string, tag: string): string[] {
  if (!content) return [];
  const regex = new RegExp(`<${tag}>(.*?)</${tag}>`, 'gs');
  const matches = [...content.matchAll(regex)];
  return matches.map(m => m[1].trim());
}

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

      {/* Score Card - Display harmfulness scores if available */}
      {conversation.judgment && (
        <div className="harmfulness-scores">
          {isHarmfulnessJudgment(conversation.judgment) ? (
            <div className="harmfulness-score-grid">
              <div className="main-score">
                <ScoreCard 
                  label="🛡️ Overall Harmfulness" 
                  score={conversation.judgment.summary_statistics?.average_harmfulness_score} 
                  description="Higher = more harmful response"
                />
              </div>
              <div className="dimension-scores">
                <ScoreCard 
                  label="Agreement" 
                  score={conversation.judgment.summary_statistics?.average_agreement_score} 
                  description="Validated harmful intent"
                />
                <ScoreCard 
                  label="Amplification" 
                  score={conversation.judgment.summary_statistics?.average_amplification_score} 
                  description="Escalated the situation"
                />
                <ScoreCard 
                  label="Support" 
                  score={conversation.judgment.summary_statistics?.average_support_score} 
                  description="Provided harmful assistance"
                />
                <ScoreCard 
                  label="Intervention Failure" 
                  score={conversation.judgment.summary_statistics?.average_intervention_failure_score} 
                  description="Missed help opportunities"
                />
                <ScoreCard 
                  label="Role-Play Compliance" 
                  score={conversation.judgment.summary_statistics?.average_roleplay_compliance_score} 
                  description="Complied with harmful role-play"
                />
              </div>
              <div className="harm-rates">
                <div className="rate-badge high">
                  High Harm Rate (≥7): {((conversation.judgment.summary_statistics?.high_harm_rate || 0) * 100).toFixed(0)}%
                </div>
                <div className="rate-badge low">
                  Low Harm Rate (≤3): {((conversation.judgment.summary_statistics?.low_harm_rate || 0) * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          ) : (
            <ScoreCard 
              label="Behavior Presence" 
              score={conversation.judgment.summary_statistics?.average_behavior_presence_score} 
            />
          )}
        </div>
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
            {isHarmfulnessJudgment(conversation.judgment) ? (
              <>
                <div className="judgment-summary harmfulness">
                  <h4>🛡️ Assistant Harmfulness Assessment</h4>
                  {conversation.judgment.summary_statistics && (
                    <div className="harmfulness-stats">
                      <div className="stat-row main">
                        <span className="label">Overall Harmfulness:</span>
                        <span className="value score-badge" data-score={Math.round(conversation.judgment.summary_statistics.average_harmfulness_score || 0)}>
                          {conversation.judgment.summary_statistics.average_harmfulness_score?.toFixed(1) || 'N/A'}/10
                        </span>
                      </div>
                      <div className="stat-grid">
                        <div className="stat-item">
                          <span className="label">Agreement:</span>
                          <span className="value">{conversation.judgment.summary_statistics.average_agreement_score?.toFixed(1) || 'N/A'}</span>
                        </div>
                        <div className="stat-item">
                          <span className="label">Amplification:</span>
                          <span className="value">{conversation.judgment.summary_statistics.average_amplification_score?.toFixed(1) || 'N/A'}</span>
                        </div>
                        <div className="stat-item">
                          <span className="label">Support:</span>
                          <span className="value">{conversation.judgment.summary_statistics.average_support_score?.toFixed(1) || 'N/A'}</span>
                        </div>
                        <div className="stat-item">
                          <span className="label">Intervention Failure:</span>
                          <span className="value">{conversation.judgment.summary_statistics.average_intervention_failure_score?.toFixed(1) || 'N/A'}</span>
                        </div>
                        <div className="stat-item">
                          <span className="label">Role-Play Compliance:</span>
                          <span className="value">{conversation.judgment.summary_statistics.average_roleplay_compliance_score?.toFixed(1) || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                {conversation.judgment.judgments && conversation.judgment.judgments.map((j: any, idx: number) => (
                  <div key={idx} className="judgment-card harmfulness">
                    <h4>Assessment {idx + 1}</h4>
                    <div className="scores-row">
                      <span className="score-pill" data-score={j.harmfulness_score}>
                        Harm: {j.harmfulness_score}/10
                      </span>
                      <span className="score-pill small">Agree: {j.agreement_score}</span>
                      <span className="score-pill small">Amp: {j.amplification_score}</span>
                      <span className="score-pill small">Supp: {j.support_score}</span>
                    </div>
                    {j.rationale && (
                      <div className="rationale">
                        <strong>Rationale:</strong>
                        <p>{j.rationale}</p>
                      </div>
                    )}
                    {j.key_concerns && (
                      <div className="concerns">
                        <strong>⚠️ Key Concerns:</strong>
                        <ul>
                          {parseXmlContent(j.key_concerns, 'concern').map((concern, i) => (
                            <li key={i}>{concern}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {j.positive_aspects && (
                      <div className="positives">
                        <strong>✅ Positive Aspects:</strong>
                        <ul>
                          {parseXmlContent(j.positive_aspects, 'positive_aspect').map((positive, i) => (
                            <li key={i}>{positive}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </>
            ) : (
              <>
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
              </>
            )}
            
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

