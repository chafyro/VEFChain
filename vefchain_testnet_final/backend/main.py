from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging
from typing import List, Dict, Optional
import time, hashlib, json
import os
from cryptography.fernet import Fernet

app = FastAPI()

# Generate a key for encryption (You should store this key securely, e.g., in an environment variable)
key = Fernet.generate_key()
cipher = Fernet(key)

# Function to load tasks from a file
def load_tasks():
    try:
        with open("data/tasks.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # Return empty list if no file exists

# Save tasks to a file
def save_tasks(tasks):
    with open("data/tasks.json", "w") as f:
        json.dump(tasks, f)

# Load tasks from JSON file (persistent)
TASKS_FILE = "data/tasks.json"
if os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, "r") as f:
        tasks = json.load(f)
else:
    tasks = []

# Blockchain logic
class VEFBlock:
    def __init__(self, index, timestamp, problem, solution, solve_steps, verify_steps, staker, previous_hash, reward, transfers, zk_proof=None):
        self.index = index
        self.timestamp = timestamp
        self.problem = problem
        self.solution = solution
        self.solve_steps = solve_steps
        self.verify_steps = verify_steps
        self.vef = solve_steps / verify_steps if verify_steps else 0
        self.reward = reward
        self.transfers = transfers
        self.staker = staker
        self.previous_hash = previous_hash
        self.zk_proof = zk_proof or {}
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_data = json.dumps(self.__dict__, sort_keys=True, default=str).encode()
        return hashlib.sha256(block_data).hexdigest()

class VEFBlockchain:
    def __init__(self):
        self.chain: List[VEFBlock] = []
        self.stakers: Dict[str, float] = {}
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = VEFBlock(0, time.time(), "GENESIS", "", 1, 1, "genesis", "0", 0, [])
        self.chain.append(genesis)

    def add_block(self, problem, solution, solve_steps, verify_steps, staker, zk_proof=None):
        last_block = self.chain[-1]
        epoch = len(self.chain)
        vef = solve_steps / verify_steps if verify_steps else 0
        reward = min(vef * (50 / (2 ** (epoch // 50))), 1000)
        new_block = VEFBlock(
            index=epoch,
            timestamp=time.time(),
            problem=problem,
            solution=solution,
            solve_steps=solve_steps,
            verify_steps=verify_steps,
            staker=staker,
            previous_hash=last_block.hash,
            reward=reward,
            transfers=[],
            zk_proof=zk_proof
        )
        self.chain.append(new_block)
        self.stakers[staker] = self.stakers.get(staker, 0) + reward
        return new_block

blockchain = VEFBlockchain()

class Submission(BaseModel):
    problem: str
    solution: List[int]
    solve_steps: int
    verify_steps: int
    staker: str
    zk_proof: Optional[dict] = {}

@app.get("/chain")
def get_chain():
    return [block.__dict__ for block in blockchain.chain]

# Setup basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/submit")
def submit_solution(data: Submission):
    # Validation check for solve_steps and verify_steps
    if data.solve_steps <= 0 or data.verify_steps <= 0:
        logger.error(f"Invalid step counts: solve_steps={data.solve_steps}, verify_steps={data.verify_steps}")
        raise HTTPException(status_code=400, detail="Invalid step counts")
    
    try:
        # Encrypt the zk_proof before saving or processing
        if data.zk_proof:
            encrypted_zk_proof = cipher.encrypt(json.dumps(data.zk_proof).encode())
        else:
            encrypted_zk_proof = None

        # Log the incoming request details
        logger.info(f"Received submission for problem {data.problem} with solution: {data.solution}")

        # Add the block to the blockchain (assuming blockchain logic exists)
        block = blockchain.add_block(
            problem=data.problem,
            solution=str(data.solution),
            solve_steps=data.solve_steps,
            verify_steps=data.verify_steps,
            staker=data.staker,
            zk_proof=encrypted_zk_proof
        )

        # Log success after block is added
        logger.info(f"Block successfully added to blockchain. Block hash: {block.hash}")
        return block.__dict__

    except Exception as e:
        # Log the error if any exception occurs
        logger.error(f"Error during block submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during block submission")
    
@app.get("/balance/{staker}")
def get_balance(staker: str):
    return {"staker": staker, "balance": blockchain.stakers.get(staker, 0)}

@app.get("/tasks")
def get_tasks():
    tasks = load_tasks()  
    return tasks

class TaskSubmission(BaseModel):
    task_id: str
    solution: List[int]
    staker: str
    solve_steps: int

@app.post("/validate")
def validate_submission(sub: TaskSubmission):
    # Log the incoming submission
    logger.info(f"Received submission for task {sub.task_id} from staker {sub.staker}")

    # Attempt to find the task
    task = next((t for t in tasks if t['id'] == sub.task_id), None)
    if not task:
        logger.error(f"Task {sub.task_id} not found.")
        raise HTTPException(status_code=404, detail="Task not found")

    # Initialize verification result and reward value
    verified = False
    reward_value = 0

    try:
        # Handle task-specific logic for validation
        if task['type'] == 'subset_sum':
            verified = sum(sub.solution) == task['data']['target'] and all(i in task['data']['nums'] for i in sub.solution)
            reward_value = len(sub.solution)
        elif task['type'] == 'knapsack':
            w = sum(task['data']['weights'][i] for i in sub.solution)
            verified = w <= task['data']['capacity']
            reward_value = sum(task['data']['values'][i] for i in sub.solution) if verified else 0
        elif task['type'] == '3sat':
            assignment = sub.solution
            verified = all(any((assignment[abs(l)-1] if l > 0 else not assignment[abs(l)-1]) for l in clause) for clause in task['data']['clauses'])
            reward_value = len(task['data']['clauses'])
        else:
            logger.error(f"Unknown task type {task['type']} for task {sub.task_id}")
            raise HTTPException(status_code=400, detail="Invalid task type")

        # Check if the solution was verified successfully
        if not verified:
            logger.warning(f"Solution verification failed for task {sub.task_id} with solution {sub.solution}")
            raise HTTPException(status_code=400, detail="Solution failed verification")

        # Calculate VEF (Verification Elevation Factor)
        vef = sub.solve_steps / reward_value if reward_value else float('inf')
        
        # Log successful validation
        logger.info(f"Solution validated for task {sub.task_id}, VEF: {vef:.2f}")
        
        return {
            "task_id": sub.task_id,
            "staker": sub.staker,
            "verified": verified,
            "solve_steps": sub.solve_steps,
            "verify_steps": reward_value,
            "vef": round(vef, 2),
            "message": "Solution verified. Submit this to the chain with these values."
        }

    except Exception as e:
        # Log any unexpected errors
        logger.error(f"Error during task validation for {sub.task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error during task validation: {str(e)}")

# Root route to respond with a welcome message
@app.get("/")
def read_root():
    return {"message": "Welcome to VEFChain API"}

# Favicon route to handle the /favicon.ico request
@app.get("/favicon.ico")
def favicon():
    return FileResponse("/miguelpinheiro/dDocuments/VEFCHAIN/vefchain_testnet_final/frontend/public/favicon.ico")
