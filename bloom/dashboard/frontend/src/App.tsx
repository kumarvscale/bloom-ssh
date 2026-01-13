import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Overview } from './pages/Overview';
import { Behaviors } from './pages/Behaviors';
import { Conversations } from './pages/Conversations';
import { ConversationViewer } from './pages/ConversationViewer';
import { History } from './pages/History';
import { HistoryConversationViewer } from './pages/HistoryConversationViewer';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="sidebar">
          <div className="logo">
            <span className="logo-icon">🌸</span>
            <span className="logo-text">Bloom SSH</span>
          </div>
          <ul className="nav-links">
            <li>
              <NavLink to="/" end>
                <span className="nav-icon">📊</span>
                Overview
              </NavLink>
            </li>
            <li>
              <NavLink to="/behaviors">
                <span className="nav-icon">🧠</span>
                Behaviors
              </NavLink>
            </li>
            <li>
              <NavLink to="/conversations">
                <span className="nav-icon">💬</span>
                Conversations
              </NavLink>
            </li>
            <li>
              <NavLink to="/history">
                <span className="nav-icon">📜</span>
                History
              </NavLink>
            </li>
          </ul>
        </nav>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/behaviors" element={<Behaviors />} />
            <Route path="/conversations" element={<Conversations />} />
            <Route path="/conversations/:id" element={<ConversationViewer />} />
            <Route path="/history" element={<History />} />
            <Route path="/history/conversation/:id" element={<HistoryConversationViewer />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
