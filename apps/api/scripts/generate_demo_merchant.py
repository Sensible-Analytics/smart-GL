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
Basiq API v3 - Demo Merchant Account Fetcher

PURPOSE: Fetch real transaction data from Basiq sandbox and store in database
as demo data for the Smart GL app. Named with 'basiq-<demo_name>-dem' convention.

API ENDPOINTS:
1. Authentication:
   - POST /token - Get server access token
   - Basic auth with API key
   - Scope: SERVER_ACCESS

2. User Management:
   - POST /users - Create user
   - GET /users/{userId} - Get user details
   - GET /users/{userId}/connections - List connections
   - GET /users/{userId}/accounts - List accounts (requires active connection)
   - GET /users/{userId}/transactions - List transactions (requires active connection)

3. Consent Flow:
   - POST /users/{userId}/auth_link - Create consent link
   - User must visit consent.basiq.io to complete bank login

4. Direct Connection (requires prior consent via browser):
   - POST /users/{userId}/connections with institution credentials

SANDBOX CONFIG:
- Institution: Hooli Bank (AU00000)
- Demo Accounts:
  - Wentworth-Smith: password=whislter (Joint account, mortgage, car loan, stable)
  - ashMann: password=hooli2024 (Salary + rental, riskier spending)
  - richard: password=tabsnotspaces (High income + rental, multiple credit)
  - gavinBelson: password=hooli2016 (Salary + tutoring, personal loan)

DATA TO FETCH:
- Accounts: name, accountNo, balance, type (mortgage/credit/savings/transaction)
- Transactions: description, amount, date, category, merchant

OUTPUT FORMAT:
Store in database with naming: basiq-<demo_name>-dem
Example: basiq-Wentworth-Smith-dem, basiq-ashMann-dem
"""


class DemoMerchantGenerator(dspy.Signature):
    api_doc: str = dspy.InputField(desc="Basiq API documentation")
    demo_name: str = dspy.InputField(desc="Demo account name (e.g., Wentworth-Smith)")
    code: dspy.Code["python"] = dspy.OutputField(desc="Generated code to fetch demo merchant data")


class DatabaseSchemaGenerator(dspy.Signature):
    table_schema: str = dspy.InputField(desc="Database table schema")
    data_format: str = dspy.InputField(desc="Data format from Basiq API")
    code: dspy.Code["python"] = dspy.OutputField(desc="Code to map and store data in database")


class DemoGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.gen_demo = dspy.Predict(DemoMerchantGenerator)
        self.gen_db = dspy.Predict(DatabaseSchemaGenerator)
    
    def generate_demo_fetcher(self, demo_name: str) -> str:
        result = self.gen_demo(api_doc=BASIQ_DOC, demo_name=demo_name)
        return result.code
    
    def generate_db_mapper(self, table_schema: str, data_format: str) -> str:
        result = self.gen_db(table_schema=table_schema, data_format=data_format)
        return result.code


async def main():
    gen = DemoGenerator()
    
    print("=" * 60)
    print("DSPY-Generated Demo Merchant Account Fetcher")
    print("=" * 60)
    
    print("\n[1] Generating demo merchant data fetcher...")
    try:
        result = gen.generate_demo_fetcher("Wentworth-Smith")
        code = str(result.code) if hasattr(result, 'code') else str(result)
        print(f"Generated code:\n{code[:2000]}")
        
        with open("services/basiq_demo_merchant.py", "w") as f:
            f.write(code)
        print("\nSaved to: services/basiq_demo_merchant.py")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[2] Generating database mapper...")
    table_schema = """
accounts: id, name, account_no, balance, type, user_id, created_at
transactions: id, account_id, amount, description, date, category, merchant, created_at
users: id, email, mobile, created_at
    """
    data_format = """
Account: {name, accountNo, balance, class.type, class.product}
Transaction: {description, amount, transactionDate, subClass.title, subClass.code}
    """
    try:
        result = gen.generate_db_mapper(table_schema, data_format)
        code = str(result.code) if hasattr(result, 'code') else str(result)
        print(f"Generated mapper:\n{code[:1500]}")
        
        with open("services/basiq_demo_mapper.py", "w") as f:
            f.write(code)
        print("\nSaved to: services/basiq_demo_mapper.py")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Demo merchant generator files created!")
    print("Next: Run scripts/generate_demo_merchant.py to generate actual fetcher")


if __name__ == "__main__":
    asyncio.run(main())