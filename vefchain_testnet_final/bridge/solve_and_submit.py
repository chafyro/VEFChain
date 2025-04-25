import requests
from functools import lru_cache

class Counter:
    def __init__(self): self.count = 0
    def tick(self): self.count += 1
    def reset(self): self.count = 0

def optimized_subset_sum(nums, target, counter):
    nums = sorted(nums, reverse=True)
    
    @lru_cache(None)
    def dfs(i, remaining):
        counter.tick()
        if remaining == 0: return []
        if remaining < 0 or i >= len(nums): return None
        with_i = dfs(i + 1, remaining - nums[i])
        if with_i is not None: return [nums[i]] + with_i
        return dfs(i + 1, remaining)
    
    return dfs(0, target)

# 1. Fetch task
try:
    res = requests.get("http://vef-api:8000/tasks")
    res.raise_for_status()
    task = res.json()[0]  # Pick the first task
except Exception as e:
    print("❌ Failed to get task:", e)
    exit(1)

nums = task["data"]["nums"]
target = task["data"]["target"]
task_id = task["id"]
staker = "ai-bot"

# 2. Solve task
counter = Counter()
solution = optimized_subset_sum(tuple(nums), target, counter)
solve_steps = counter.count

# 3. Verify solution with backend
verify = requests.post("http://vef-api:8000/validate", json={
    "task_id": task_id,
    "solution": solution,
    "staker": staker,
    "solve_steps": solve_steps
})

if verify.ok:
    v = verify.json()
    # 4. Submit to chain
    submit = requests.post("http://vef-api:8000/submit", json={
        "problem": task_id,
        "solution": solution,
        "solve_steps": solve_steps,
        "verify_steps": v["verify_steps"],
        "staker": staker,
        "zk_proof": {
            "proof": "auto",
            "inputs": solution
        }
    })
    print("✅ Submission result:", submit.json())
else:
    print("❌ Verification failed:", verify.text)
