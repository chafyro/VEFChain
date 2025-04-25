import requests
import time

def wait_for_api():
    for i in range(10):
        try:
            r = requests.get('http://vef-api:8000/tasks')
            if r.ok:
                return r.json()
        except Exception:
            print(f"⏳ API not ready yet... retrying ({i + 1}/10)")
            time.sleep(2)
    raise RuntimeError("❌ Could not connect to API.")

def solve_subset_sum(nums, target):
    nums = sorted(nums, reverse=True)
    def dfs(i, current, path):
        if current == target:
            return path
        if current > target or i >= len(nums):
            return None
        # Try including this number
        with_num = dfs(i + 1, current + nums[i], path + [nums[i]])
        if with_num:
            return with_num
        return dfs(i + 1, current, path)
    return dfs(0, 0, [])

def main():
    tasks = wait_for_api()
    task = next((t for t in tasks if t['type'] == 'subset_sum'), None)

    if not task:
        print("❌ No subset_sum task found.")
        return

    nums = task['data']['nums']
    target = task['data']['target']
    task_id = task['id']

    solution = solve_subset_sum(nums, target)
    if not solution:
        print("❌ Could not find a valid solution.")
        return

    try:
        validate = requests.post("http://vef-api:8000/validate", json={
            "task_id": task_id,
            "solution": solution,
            "staker": "ai-bridge",
            "solve_steps": len(solution) * 5
        })

        if not validate.ok:
            print("❌ Validation failed:", validate.text)
            return

        data = validate.json()
        print("✅ Validated:", data)

        submit = requests.post("http://vef-api:8000/submit", json={
            "problem": task_id,
            "solution": solution,
            "solve_steps": data["solve_steps"],
            "verify_steps": data["verify_steps"],
            "staker": "ai-bridge",
            "zk_proof": {"proof": "bridge-auto", "inputs": solution}
        })

        print("📦 Block submitted:", submit.json())

    except Exception as e:
        print("❌ Error during validate/submit:", str(e))

if __name__ == "__main__":
    main()
