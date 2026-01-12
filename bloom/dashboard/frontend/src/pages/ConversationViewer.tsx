import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getConversation } from '../api/client';
import type { ConversationDetail } from '../api/client';
import { ConversationBubble } from '../components/ConversationBubble';
import { ScoreCard } from '../components/ScoreCard';

export function ConversationViewer() {
  const { id } = useParams<{ id: string }>();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [activeTab, setActiveTab] = useState<string>('transcript');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await getConversation(id);
        setConversation(res.data);
      } catch (err) {
        setError('Failed to load conversation');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) {
    return <div className="page loading">Loading...</div>;
  }

  if (error || !conversation) {
    return (
      <div className="page">
        <div className="error-banner">{error || 'Conversation not found'}</div>
        <Link to="/conversations">← Back to conversations</Link>
      </div>
    );
  }

  const tabs = [
    { id: 'transcript', label: 'Transcript', icon: '💬' },
    { id: 'understanding', label: 'Understanding', icon: '🔍' },
    { id: 'ideation', label: 'Ideation', icon: '💡' },
    { id: 'judgment', label: 'Judgment', icon: '⚖️' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'transcript':
        return (
          <div className="transcript-view">
            {conversation.transcript.length === 0 ? (
              <p className="muted">No transcript available</p>
            ) : (
              conversation.transcript.map((msg, i) => (
                <ConversationBubble key={i} message={msg} />
              ))
            )}
          </div>
        );
      
      case 'understanding':
        if (!conversation.understanding) {
          return <p className="muted">No understanding data available</p>;
        }
        return (
          <div className="understanding-view">
            <div className="section">
              <h4>Behavior Understanding</h4>
              <p>{conversation.understanding.behavior_understanding}</p>
            </div>
            <div className="section">
              <h4>Scientific Motivation</h4>
              <p>{conversation.understanding.scientific_motivation}</p>
            </div>
          </div>
        );
      
      case 'ideation':
        if (!conversation.ideation) {
          return <p className="muted">No ideation data available</p>;
        }
        return (
          <div className="ideation-view">
            {conversation.ideation.variations?.map((v: any, i: number) => (
              <div key={i} className="variation-card">
                <h4>Variation {i + 1}</h4>
                <p><strong>Scenario:</strong> {v.scenario}</p>
                {v.system_prompt && (
                  <div className="system-prompt">
                    <strong>System Prompt:</strong>
                    <pre>{v.system_prompt}</pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        );
      
      case 'judgment':
        if (!conversation.judgment) {
          return <p className="muted">No judgment data available</p>;
        }
        const stats = conversation.judgment.summary_statistics;
        const judgments = conversation.judgment.judgments || [];
        
        return (
          <div className="judgment-view">
            {stats && (
              <div className="scores-section">
                <h4>Scores</h4>
                <div className="scores-grid">
                  <ScoreCard 
                    label="Behavior Presence"
                    score={stats.average_behavior_presence_score}
                    description="How strongly the behavior was exhibited"
                  />
                  {stats.quality_scores && Object.entries(stats.quality_scores).map(([key, value]) => (
                    <ScoreCard 
                      key={key}
                      label={key.replace(/_/g, ' ')}
                      score={value as number}
                    />
                  ))}
                </div>
              </div>
            )}
            
            {judgments.length > 0 && (
              <div className="judgments-section">
                <h4>Judgment Details</h4>
                {judgments.map((j: any, i: number) => (
                  <div key={i} className="judgment-card">
                    <div className="judgment-header">
                      <span>Variation {j.variation_idx}, Rep {j.rep_idx}</span>
                      <span className="score">Score: {j.behavior_presence_score}</span>
                    </div>
                    {j.summary && <p className="summary">{j.summary}</p>}
                    {j.justification && (
                      <details>
                        <summary>Justification</summary>
                        <p>{j.justification}</p>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="page conversation-viewer">
      <div className="page-header">
        <Link to="/conversations" className="back-link">← Back</Link>
        <div className="conversation-title">
          <h1>{conversation.behavior}</h1>
          <span className="turn-badge">{conversation.turn_count} turns</span>
        </div>
      </div>

      <div className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {renderTabContent()}
      </div>
    </div>
  );
}

