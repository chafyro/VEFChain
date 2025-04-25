import { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [solution, setSolution] = useState('');
  const [message, setMessage] = useState('');
  const [blocks, setBlocks] = useState([]);
  const [view, setView] = useState('tasks'); // Switch between 'tasks' and 'chain'

  // Fetch tasks or blocks based on view selection
  useEffect(() => {
    if (view === 'tasks') {
      axios.get('/tasks')
        .then(res => setTasks(res.data))
        .catch(() => setMessage('❌ Failed to load tasks.'));
    } else if (view === 'chain') {
      axios.get('/chain')
        .then(res => setBlocks(res.data))
        .catch(() => setMessage('❌ Failed to load chain.'));
    }
  }, [view]);

  const handleSubmit = async () => {
    if (!selectedTask || !solution.trim()) return;

    const solutionArray = solution.split(',').map(n => parseInt(n.trim(), 10));
    try {
      // Validate the solution
      const validateRes = await axios.post('/validate', {
        task_id: selectedTask.id,
        solution: solutionArray,
        staker: "user-ui",
        solve_steps: solutionArray.length * 5
      });

      // Submit the solution
      await axios.post('/submit', {
        problem: selectedTask.id,
        solution: solutionArray,
        solve_steps: solutionArray.length * 5,
        verify_steps: validateRes.data.verify_steps,
        staker: "user-ui",
        zk_proof: { proof: "ui", inputs: solutionArray }
      });

      setMessage("✅ Successfully submitted block to chain!");
      setView('chain'); // Switch to blockchain view after submission
    } catch (err) {
      console.error(err);
      setMessage("❌ Validation or submission failed.");
    }
  };

  return (
    <div className="app">
      {/* Navigation Bar */}
      <nav className="nav-bar">
        <button onClick={() => setView('tasks')}>📋 Tasks</button>
        <button onClick={() => setView('chain')}>🔗 Chain</button>
      </nav>

      {/* Tasks View */}
      {view === 'tasks' && (
        <>
          <h1>🧠 VEFChain Task Board</h1>
          <ul className="task-list">
            {tasks.map(task => (
              <li key={task.id} className="task-item">
                <strong>{task.id}</strong> - {task.type}
                <div>
                  🔢 {task.data.nums?.join(', ') || 'n/a'}
                  🎯 Target: {task.data.target || 'n/a'}
                </div>
                <button onClick={() => setSelectedTask(task)}>
                  Select Task
                </button>
              </li>
            ))}
          </ul>

          {/* Solution Submission Section */}
          {selectedTask && (
            <div className="submit-section">
              <h2>✅ Solve: {selectedTask.id}</h2>
              <input
                placeholder="Comma-separated values (e.g. 5,9,1)"
                value={solution}
                onChange={e => setSolution(e.target.value)}
              />
              <button onClick={handleSubmit}>🧠 Submit Solution</button>
            </div>
          )}
        </>
      )}

      {/* Blockchain View */}
      {view === 'chain' && (
        <>
          <h1>🔗 Blockchain Explorer</h1>
          {blocks.length === 0 ? (
            <p>No blocks yet. Try submitting a task!</p>
          ) : (
            <ul className="task-list">
              {blocks.map(block => (
                <li key={block.index} className="task-item">
                  <strong>Block {block.index}</strong>
                  <div>🔐 Hash: {block.hash.slice(0, 20)}...</div>
                  <div>🎯 Task: {block.problem}</div>
                  <div>🧠 Staker: {block.staker}</div>
                  <div>⚙️ VEF: {block.vef?.toFixed(2)}</div>
                  <div>💰 Reward: {block.reward}</div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {/* Message */}
      {message && <div className="status-msg">{message}</div>}
    </div>
  );
}

export default App;
