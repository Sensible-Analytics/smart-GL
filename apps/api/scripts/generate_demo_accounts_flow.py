import os
import dspy

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    dspy.configure(lm=dspy.LM("groq/llama-3.1-8b-instant", api_key=GROQ_API_KEY))
else:
    print("ERROR: No GROQ_API_KEY")
    exit(1)

DEMO_ACCOUNTS_FLOW_DOC = """
DSPY-Generated Demo Accounts Flow: Basiq -> Neon -> API -> UI

PURPOSE: Fetch demo account data from Basiq sandbox (via Neon database)
and serve via API endpoints for the Smart GL web app.

NEON DATABASE (smart-gl project: misty-hall-97596041):
- Project: smart-gl
- Database: neondb
- Table: demo_accounts
  Columns: id, name, account_no, balance, type, institution, created_at

BASIQ SANDBOX (already connected):
- User: 11b17186-1c3b-4951-a670-b597d70e07e3
- Institution: Hooli Bank (AU00000)
- Demo accounts (Wentworth-Smith):
  - Mortgage: 033057-001, -$769,000
  - Credit Card: 033057-002, -$1,300
  - Savings: 033057-003, +$3,200
  - Transaction: 033057-004, +$33,500

API PATTERN (FastAPI + Neon serverless driver):
- Use @neondatabase/serverless for async Neon queries
- Connection pooling via pooler endpoint

REQUIRED COMPONENTS:
1. services/demo_accounts_service.py - Neon DB queries for demo accounts
2. routers/demo_accounts.py - FastAPI router for /demo-accounts endpoint
3. Update main.py to include the new router

OUTPUT: Generated code that follows existing patterns in the codebase.
"""


class DemoAccountsFlowGenerator(dspy.Signature):
    api_doc: str = dspy.InputField(desc="Demo accounts flow documentation")
    component: str = dspy.InputField(desc="Component to generate (service or router)")
    code: dspy.Code["python"] = dspy.OutputField(desc="Generated Python code")


class DemoAccountsFlowModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.gen = dspy.Predict(DemoAccountsFlowGenerator)
    
    def generate(self, component: str) -> str:
        result = self.gen(api_doc=DEMO_ACCOUNTS_FLOW_DOC, component=component)
        return str(result.code)


def main():
    gen = DemoAccountsFlowModule()
    
    print("=" * 60)
    print("DSPY Demo Accounts Flow Generator")
    print("=" * 60)
    
    print("\n[1] Generating demo accounts service...")
    try:
        code = gen.generate("service")
        print(f"Generated service code:\n{code[:1500]}")
        with open("services/demo_accounts_service.py", "w") as f:
            f.write(code)
        print("\nSaved to: services/demo_accounts_service.py")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[2] Generating demo accounts router...")
    try:
        code = gen.generate("router")
        print(f"Generated router code:\n{code[:1500]}")
        with open("routers/demo_accounts.py", "w") as f:
            f.write(code)
        print("\nSaved to: routers/demo_accounts.py")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Demo accounts flow generated!")
    print("Next: Verify and run the API")


if __name__ == "__main__":
    main()