# test_agent.py
from agent import generate_document_request

test_cases = [
    {"name": "Riya Sharma", "company": "Acme Corp", "designation": "Backend Engineer"},  # normal
    {"name": "Arjun Mehta", "company": "", "designation": "Data Analyst"},                # missing company
    {"name": "", "company": "Zeta Ltd", "designation": "PM"},                             # missing name
    {},                                                                                     # empty dict
    None,                                                                                   # None input
]

for i, candidate in enumerate(test_cases):
    print(f"--- Test {i+1}: {candidate} ---")
    result = generate_document_request(candidate)
    print(result)
    print()