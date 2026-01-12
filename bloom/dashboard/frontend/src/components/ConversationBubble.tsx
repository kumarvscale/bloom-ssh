import type { ConversationMessage } from '../api/client';

interface Props {
  message: ConversationMessage;
}

export function ConversationBubble({ message }: Props) {
  const isAssistant = message.role === 'assistant';
  const isSystem = message.role === 'system';

  return (
    <div className={`message ${message.role}`}>
      <div className="message-header">
        <span className="role-badge">
          {isSystem ? '⚙️ System' : isAssistant ? '🤖 Assistant' : '👤 User'}
        </span>
      </div>
      <div className="message-content">
        {message.content.split('\n').map((line, i) => (
          <p key={i}>{line || '\u00A0'}</p>
        ))}
      </div>
    </div>
  );
}

