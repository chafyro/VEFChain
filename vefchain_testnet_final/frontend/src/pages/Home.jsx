import { useEffect, useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [solution, setSolution] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchTasks();
  }, []);

  async function fetchTasks() {
    try {
      const res = await axios.get('/tasks');
      setTasks(res.data);
    } catch (err) {
      console.error('Error fetching tasks:', err);
    }
  }

  async function handleValidateAndSubmit() {
    if (!selectedTask || solution.trim() === "") return;

    const solutionArray = solution.split(',').map(n => parseInt(n.trim(), 10));
    try {
      const validateRes = await axios.post('/validate', {
        task_id: selectedTask.id,
        solution: solutionArray,
        staker: "user-frontend",
        solve_steps: solutionArray.length * 5
      });
      console.log('Validation:', validateRes.data);

      await axios.post('/submit', {
        problem: selectedTask.id,
        solution: solutionArray,
        solve_steps: solutionArray.length * 5,
        verify_steps: validateRes.data.verify_steps,
        staker: "user-frontend",
        zk_proof: { proof: "frontend-submit", inputs: solutionArray }
      });

      setMessage("✅ Successfully submitted to chain!");
    } catch (err) {
      console.error('Error submitting:', err);
      setMessage("❌ Error validating or submitting.");
    }
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">📋 Available Tasks</h1>

      <ul className="space-y-2">
        {tasks.map(task => (
          <li key={task.id} className="border p-2 rounded">
            <div>
              <strong>ID:</strong> {task.id}
            </div>
            <div>
              <strong>Numbers:</strong> {task.data.nums?.join(', ') || "N/A"}
            </div>
            <div>
              <strong>Target:</strong> {task.data.target || "N/A"}
            </div>
            <button
              className="mt-2 px-2 py-1 bg-blue-500 text-white rounded"
              onClick={() => setSelectedTask(task)}
            >
              Select Task
            </button>
          </li>
        ))}
      </ul>

      {selectedTask && (
        <div className="mt-8">
          <h2 className="text-xl mb-2">Selected Task: {selectedTask.id}</h2>
          <input
            className="border p-2 w-full mb-2"
            placeholder="Enter your solution (e.g., 5,9,3)"
            value={solution}
            onChange={e => setSolution(e.target.value)}
          />
          <button
            className="px-4 py-2 bg-green-600 text-white rounded"
            onClick={handleValidateAndSubmit}
          >
            ✅ Validate & Submit
          </button>
          {message && <div className="mt-4">{message}</div>}
        </div>
      )}
    </div>
  );
}
