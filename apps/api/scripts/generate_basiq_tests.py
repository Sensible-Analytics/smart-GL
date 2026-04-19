import os
import dspy
import asyncio

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    dspy.configure(lm=dspy.LM("groq/llama-3.1-8b-instant", api_key=GROQ_API_KEY))
else:
    print("ERROR: No GROQ_API_KEY")
    exit(1)

BASIQ_DOC = """
Basiq API v3 Testing - SANDBOX MODE:

1. Sandbox Environment: Use your sandbox API key (starts with test_)
2. Test Bank: Hooli Bank (institution ID: AU00000)
3. Test Users (sandbox personas with credentials):
   - ashMann: password=hooli2024 (Salary + rental income, riskier spending)
   - richard: password=tabsnotspaces (High stable income + rental)
   - jared: password=django (Uber income, mortgage, volatile earnings)
   - gavinBelson: password=hooli2016 (Salary + tutoring, personal loan)
   - Gilfoyle: password=PiedPiper (Unemployment benefits, BNPL with late fees)
   - Whistler: password=ShowBox (Fortnightly salary, BNPL, large transfers)
   - Wentworth-Smith: password=whislter (Joint account, stable income, mortgage, car loan)

4. Test Flow (Automated via API):
   a. POST /token with sandbox API key -> get access_token
   b. POST /users -> create test user
   c. POST /users/{userId}/connections -> create connection with institution and credentials
   d. Wait for job to complete (poll /jobs/{jobId})
   e. Once connection is active: GET /users/{userId}/accounts
   f. For identity: GET /users/{userId}/identity (needs verified connection)

5. Direct Connection Creation (bypasses consent UI):
   POST /users/{userId}/connections
   {
     "institution": {"id": "AU00000"},
     "credentials": {"id": "test-user", "password": "test-password"}
   }

6. Institutions List: GET /institutions (sandbox returns test banks only)
"""

class BasiqTestGenerator(dspy.Signature):
    api_doc: str = dspy.InputField(desc="Basiq API documentation")
    test_scenario: str = dspy.InputField(desc="What to test (accounts, identity, connection)")
    code: dspy.Code["python"] = dspy.OutputField(desc="Generated test code using sandbox credentials")


class BasiqFlowAnalyzer(dspy.Signature):
    api_doc: str = dspy.InputField(desc="Basiq API docs")
    challenge: str = dspy.InputField(desc="What needs to be tested")
    solution: dspy.Code["python"] = dspy.OutputField(desc="Code to solve the challenge")


class TestGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.gen_test = dspy.Predict(BasiqTestGenerator)
        self.analyze = dspy.Predict(BasiqFlowAnalyzer)
    
    def generate_test(self, scenario: str) -> str:
        result = self.gen_test(api_doc=BASIQ_DOC, test_scenario=scenario)
        return result.code
    
    def analyze_flow(self, challenge: str) -> str:
        result = self.analyze(api_doc=BASIQ_DOC, challenge=challenge)
        return result.solution


async def main():
    gen = TestGenerator()
    
    print("=" * 60)
    print("DSPY-generated Basiq Integration Tests")
    print("=" * 60)
    
    print("\n[1] Analyzing how to test account/identity flow...")
    try:
        result = gen.analyze_flow(
            "How to test get_accounts and get_identity when they require an active bank connection?"
        )
        solution = str(result.solution) if hasattr(result, 'solution') else str(result)
        print(f"Analysis:\n{solution[:1500]}")
        
        with open("services/basiq_test_flow.py", "w") as f:
            f.write(solution)
        print("\nSaved to: services/basiq_test_flow.py")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[2] Generating account test...")
    try:
        result = gen.generate_test("test get_accounts with active connection")
        test_code = str(result.code) if hasattr(result, 'code') else str(result)
        print(f"Test code:\n{test_code[:1500]}")
        
        with open("services/basiq_accounts_test.py", "w") as f:
            f.write(test_code)
        print("\nSaved to: services/basiq_accounts_test.py")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[3] Generating identity test...")
    try:
        result = gen.generate_test("test get_identity with verified user")
        test_code = str(result.code) if hasattr(result, 'code') else str(result)
        print(f"Test code:\n{test_code[:1500]}")
        
        with open("services/basiq_identity_test.py", "w") as f:
            f.write(test_code)
        print("\nSaved to: services/basiq_identity_test.py")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Generated test files - review and run!")


if __name__ == "__main__":
    asyncio.run(main())