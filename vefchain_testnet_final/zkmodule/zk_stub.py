def generate_zk_proof(input_data):
    return {"proof": "zk-stub", "inputs": input_data, "verified": True}

def verify_zk_proof(proof):
    return proof.get("verified", False)