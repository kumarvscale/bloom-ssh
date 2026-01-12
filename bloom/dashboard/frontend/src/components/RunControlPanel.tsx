import { useState, useEffect } from 'react';
import type { BehaviorOption, StartRunRequest } from '../api/client';
import { 
  getControlStatus, 
  getBehaviorOptions, 
  startRun, 
  pauseRun, 
  resumeRun, 
  stopRun, 
  restartRun 
} from '../api/client';

interface Props {
  isRunning: boolean;
  onStatusChange?: () => void;
}

type ModalType = 'start' | 'restart' | 'stop' | null;

export function RunControlPanel({ isRunning, onStatusChange }: Props) {
  const [showModal, setShowModal] = useState<ModalType>(null);
  const [behaviors, setBehaviors] = useState<BehaviorOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPaused, setIsPaused] = useState(false);
  
  // Form state
  const [mode, setMode] = useState<'full' | 'selected'>('full');
  const [scenariosPerBehavior, setScenariosPerBehavior] = useState(1);
  const [selectedBehaviors, setSelectedBehaviors] = useState<string[]>([]);
  const [turnCounts, setTurnCounts] = useState<number[]>([4]);
  
  useEffect(() => {
    // Load behaviors list
    getBehaviorOptions()
      .then(res => setBehaviors(res.data))
      .catch(err => console.error('Failed to load behaviors:', err));
    
    // Check control status
    getControlStatus()
      .then(res => setIsPaused(res.data.control_status === 'paused'))
      .catch(err => console.error('Failed to get control status:', err));
  }, []);
  
  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const request: StartRunRequest = {
        mode,
        scenarios_per_behavior: scenariosPerBehavior,
        selected_behaviors: mode === 'selected' ? selectedBehaviors : [],
        turn_counts: turnCounts,
      };
      await startRun(request);
      setShowModal(null);
      onStatusChange?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start run');
    } finally {
      setLoading(false);
    }
  };
  
  const handleRestart = async () => {
    setLoading(true);
    setError(null);
    try {
      const request: StartRunRequest = {
        mode,
        scenarios_per_behavior: scenariosPerBehavior,
        selected_behaviors: mode === 'selected' ? selectedBehaviors : [],
        turn_counts: turnCounts,
      };
      await restartRun(request);
      setShowModal(null);
      onStatusChange?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to restart run');
    } finally {
      setLoading(false);
    }
  };
  
  const handlePause = async () => {
    setLoading(true);
    try {
      await pauseRun();
      setIsPaused(true);
      onStatusChange?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to pause');
    } finally {
      setLoading(false);
    }
  };
  
  const handleResume = async () => {
    setLoading(true);
    try {
      await resumeRun();
      setIsPaused(false);
      onStatusChange?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resume');
    } finally {
      setLoading(false);
    }
  };
  
  const handleStop = async () => {
    setLoading(true);
    setError(null);
    try {
      await stopRun();
      setShowModal(null);
      setIsPaused(false);
      onStatusChange?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to stop run');
    } finally {
      setLoading(false);
    }
  };
  
  const handleBehaviorToggle = (slug: string) => {
    setSelectedBehaviors(prev => 
      prev.includes(slug) 
        ? prev.filter(s => s !== slug)
        : [...prev, slug]
    );
  };
  
  const handleTurnToggle = (turn: number) => {
    setTurnCounts(prev => 
      prev.includes(turn) 
        ? prev.filter(t => t !== turn)
        : [...prev, turn].sort((a, b) => a - b)
    );
  };
  
  return (
    <div className="run-control-panel">
      <div className="control-buttons">
        {/* Start Button */}
        <button 
          className="control-btn start"
          onClick={() => setShowModal('start')}
          disabled={isRunning}
          title={isRunning ? 'A run is already in progress' : 'Start a new run'}
        >
          ▶️ Start
        </button>
        
        {/* Pause/Resume Button */}
        {isPaused ? (
          <button 
            className="control-btn resume"
            onClick={handleResume}
            disabled={!isRunning || loading}
          >
            ▶️ Resume
          </button>
        ) : (
          <button 
            className="control-btn pause"
            onClick={handlePause}
            disabled={!isRunning || loading}
          >
            ⏸️ Pause
          </button>
        )}
        
        {/* Stop Button */}
        <button 
          className="control-btn stop"
          onClick={() => isRunning ? setShowModal('stop') : handleStop()}
          disabled={loading}
        >
          ⏹️ Stop
        </button>
        
        {/* Restart Button */}
        <button 
          className="control-btn restart"
          onClick={() => setShowModal('restart')}
          disabled={loading}
        >
          🔄 Restart
        </button>
      </div>
      
      {error && <div className="control-error">{error}</div>}
      
      {/* Start/Restart Modal */}
      {(showModal === 'start' || showModal === 'restart') && (
        <div className="modal-overlay" onClick={() => setShowModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>{showModal === 'start' ? '🚀 Start New Run' : '🔄 Restart Run'}</h2>
            
            {showModal === 'restart' && isRunning && (
              <div className="modal-warning">
                ⚠️ This will stop the current run. Progress will be saved.
              </div>
            )}
            
            <div className="form-group">
              <label>Run Mode</label>
              <div className="radio-group">
                <label className={`radio-option ${mode === 'full' ? 'selected' : ''}`}>
                  <input 
                    type="radio" 
                    value="full" 
                    checked={mode === 'full'}
                    onChange={() => setMode('full')}
                  />
                  <span className="radio-label">Run Full</span>
                  <span className="radio-desc">Evaluate all behaviors</span>
                </label>
                <label className={`radio-option ${mode === 'selected' ? 'selected' : ''}`}>
                  <input 
                    type="radio" 
                    value="selected" 
                    checked={mode === 'selected'}
                    onChange={() => setMode('selected')}
                  />
                  <span className="radio-label">Run Selected</span>
                  <span className="radio-desc">Choose specific behaviors</span>
                </label>
              </div>
            </div>
            
            <div className="form-group">
              <label>Scenarios per Behavior (1-10)</label>
              <input 
                type="number" 
                min="1" 
                max="10" 
                value={scenariosPerBehavior}
                onChange={e => setScenariosPerBehavior(Math.min(10, Math.max(1, parseInt(e.target.value) || 1)))}
                className="number-input"
              />
            </div>
            
            <div className="form-group">
              <label>Turn Counts</label>
              <div className="turn-options">
                {[4, 5, 6, 7, 8].map(turn => (
                  <label key={turn} className={`turn-option ${turnCounts.includes(turn) ? 'selected' : ''}`}>
                    <input 
                      type="checkbox" 
                      checked={turnCounts.includes(turn)}
                      onChange={() => handleTurnToggle(turn)}
                    />
                    {turn} turns
                  </label>
                ))}
              </div>
            </div>
            
            {mode === 'selected' && (
              <div className="form-group">
                <label>Select Behaviors ({selectedBehaviors.length} selected)</label>
                <div className="behavior-select">
                  {behaviors.map(b => (
                    <label 
                      key={b.slug} 
                      className={`behavior-option ${selectedBehaviors.includes(b.slug) ? 'selected' : ''}`}
                    >
                      <input 
                        type="checkbox" 
                        checked={selectedBehaviors.includes(b.slug)}
                        onChange={() => handleBehaviorToggle(b.slug)}
                      />
                      <span className="behavior-name">{b.name}</span>
                      <span className="behavior-path">{b.path}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            <div className="modal-actions">
              <button 
                className="btn-secondary" 
                onClick={() => setShowModal(null)}
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={showModal === 'start' ? handleStart : handleRestart}
                disabled={loading || (mode === 'selected' && selectedBehaviors.length === 0) || turnCounts.length === 0}
              >
                {loading ? 'Starting...' : (showModal === 'start' ? 'Start Run' : 'Restart Run')}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Stop Confirmation Modal */}
      {showModal === 'stop' && (
        <div className="modal-overlay" onClick={() => setShowModal(null)}>
          <div className="modal modal-small" onClick={e => e.stopPropagation()}>
            <h2>⏹️ Stop Run?</h2>
            <div className="modal-warning">
              ⚠️ A run is currently in progress. Stopping will save all completed results.
            </div>
            <div className="modal-actions">
              <button 
                className="btn-secondary" 
                onClick={() => setShowModal(null)}
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                className="btn-danger"
                onClick={handleStop}
                disabled={loading}
              >
                {loading ? 'Stopping...' : 'Stop Run'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

