import { useEffect, useState } from 'react';
import axios from 'axios';

export default function Chain() {
  const [blocks, setBlocks] = useState([]);

  useEffect(() => {
    axios.get('/chain')
      .then(res => setBlocks(res.data))
      .catch(() => console.error("❌ Failed to fetch blockchain data"));
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">🔗 Blockchain Explorer</h1>

      {blocks.length === 0 ? (
        <p>No blocks found yet.</p>
      ) : (
        <ul className="space-y-4">
          {blocks.map((block, index) => (
            <li key={index} className="p-4 border rounded bg-white shadow">
              <div><strong>Index:</strong> {block.index}</div>
              <div><strong>Problem:</strong> {block.problem}</div>
              <div><strong>Staker:</strong> {block.staker}</div>
              <div><strong>Solution:</strong> {JSON.stringify(block.solution)}</div>
              <div><strong>VEF:</strong> {block.vef?.toFixed(2)}</div>
              <div><strong>Reward:</strong> {block.reward}</div>
              <div><strong>Hash:</strong> <small>{block.hash}</small></div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
