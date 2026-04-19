import os
import dspy

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    dspy.configure(lm=dspy.LM("groq/llama-3.1-8b-instant", api_key=GROQ_API_KEY))
else:
    print("ERROR: No GROQ_API_KEY")
    exit(1)

DEMO_ACCOUNTS_UI_DOC = """
DSPY-Generated Demo Accounts UI Component

PURPOSE: Display demo accounts from Basiq sandbox in bank-feeds page
as ADDITIONAL accounts (NOT overriding real connected accounts).

NEON DATABASE (smart-gl: misty-hall-97596041):
- Table: demo_accounts
- Columns: id, name, account_no, balance, type, institution

BASIQ SANDBOX DATA:
- Institution: Hooli Bank (AU00000)
- Demo: Wentworth-Smith (username: whislter)
- Accounts:
  - Mortgage: 033057-001, -$769,000, type: mortgage
  - Credit Card: 033057-002, -$1,300, type: credit  
  - Savings: 033057-003, +$3,200, type: savings
  - Transaction: 033057-004, +$33,500, type: transaction

API ENDPOINT: /demo/demo-accounts
Returns: { id, name, account_no, balance, type, institution }[]

UI REQUIREMENTS:
1. Show demo accounts in a separate "Demo Accounts" section
2. Display source information:
   - "Source: Basiq Sandbox (Hooli Bank)"
   - "Data queried via: Neon database"
   - "Account: Wentworth-Smith demo persona"
3. Use distinct styling (e.g., dashed border, different background)
4. Add expandable "How this data was obtained" info panel
5. DO NOT override or replace real connected accounts
6. Use existing bank-feeds page component patterns

EXISTING COMPONENT PATTERNS (bank-feeds/page.tsx):
- Grid layout with card components
- Bank name, account name, number masked, balance display
- Status badges (active/pending)
- Info footer with source details
"""


class DemoAccountsUIGenerator(dspy.Signature):
    docs: str = dspy.InputField(desc="Demo accounts UI documentation")
    component: str = dspy.InputField(desc="Component to generate")
    code: dspy.Code["typescript"] = dspy.OutputField(desc="Generated TypeScript/React code")


class DemoAccountsUIModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.gen = dspy.Predict(DemoAccountsUIGenerator)
    
    def generate(self, component: str) -> str:
        result = self.gen(docs=DEMO_ACCOUNTS_UI_DOC, component=component)
        return result.code


def main():
    gen = DemoAccountsUIModule()
    
    print("=" * 60)
    print("DSPY Demo Accounts UI Generator")
    print("=" * 60)
    
    print("\n[1] Generating demo accounts panel component...")
    try:
        code = gen.generate("DemoAccountsPanel")
        code_str = str(code)
        print(f"Generated code:\n{code_str}")
        with open("/Users/prabhatranjan/Business/sensibleAnalytics/smart-GL/apps/web/components/DemoAccountsPanel.tsx", "w") as f:
            f.write(code_str)
        print("\nSaved to: apps/web/components/DemoAccountsPanel.tsx")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Demo accounts UI component generated!")
    print("Next: Add to bank-feeds page")


if __name__ == "__main__":
    main()