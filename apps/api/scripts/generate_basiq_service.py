import os
import dspy

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    dspy.configure(lm=dspy.LM("groq/llama-3.1-8b-instant", api_key=GROQ_API_KEY))
elif os.environ.get("OLLAMA_API_KEY"):
    dspy.configure(lm=dspy.LM("ollama/llama3.2", api_key="local"))
else:
    print("ERROR: No LLM API key found (GROQ or OLLAMA)")
    exit(1)

BASIQ_API_DOC = """
Basiq API v3 Endpoints:

1. Authentication
   - POST /token - Get access token (Basic auth with API key)
     Request: grant_type=scope, scope=SERVER_ACCESS
     Response: access_token, expires_in

2. Users
   - POST /users - Create user (email, mobile required)
   - GET /users/{userId} - Get user details
   - DELETE /users/{userId} - Delete user

3. Connections (Bank Links)
   - POST /users/{userId}/connections - Create connection (institutionId, loginId, password)
   - GET /users/{userId}/connections - List connections
   - GET /users/{userId}/connections/{connectionId} - Get connection status
   - DELETE /users/{userId}/connections/{connectionId} - Unlink account

4. Accounts
   - GET /users/{userId}/accounts - List accounts
   - GET /users/{userId}/accounts/{accountId} - Get account details

5. Transactions
   - GET /users/{userId}/transactions - List transactions
     Params: filter, limit, after, before
     Filter: transaction.postDate.gte:{date}, transaction.postDate.lte:{date}
   - GET /users/{userId}/transactions/{transactionId} - Get transaction details

6. Identity
   - GET /users/{userId}/identity - Get user identity/verified name

7. Affordability (Optional)
   - POST /users/{userId}/affordability - Create affordability report
   - GET /users/{userId}/affordability/{jobId} - Get affordability result

Headers required:
- Authorization: Bearer {access_token}
- Basiq-Version: 3.0
- Content-Type: application/json

Base URL: https://au-api.basiq.io
"""

class BasiqAPISignature(dspy.Signature):
    api_doc: str = dspy.InputField(desc="Basiq API documentation")
    language: str = dspy.InputField(desc="Programming language", default="python")
    code: dspy.Code["python"] = dspy.OutputField(desc="Generated API client code")


class BasiqServiceEnhancer(dspy.Signature):
    current_code: str = dspy.InputField(desc="Current implementation")
    api_doc: str = dspy.InputField(desc="Basiq API documentation")
    enhanced_code: dspy.Code["python"] = dspy.OutputField(desc="Enhanced code")


class BasiqCodeGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.Predict(BasiqAPISignature)
        self.enhance = dspy.Predict(BasiqServiceEnhancer)
    
    def generate_service(self) -> str:
        result = self.generate(api_doc=BASIQ_API_DOC, language="python")
        return result.code
    
    def enhance_service(self, current_code: str) -> str:
        result = self.enhance(current_code=current_code, api_doc=BASIQ_API_DOC)
        return result.enhanced_code


def main():
    generator = BasiqCodeGenerator()
    
    print("[1] Generating Basiq service code...")
    try:
        result = generator.generate_service()
        generated_code = str(result.code)
        print("Generated code:\n")
        print(generated_code[:2000])
        output_path = "services/basiq_generated.py"
        with open(output_path, "w") as f:
            f.write(generated_code)
        print(f"\nSaved to: {output_path}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n[2] Enhancing existing basiq.py...")
    try:
        with open("services/basiq.py", "r") as f:
            current_code = f.read()
        result = generator.enhance_service(current_code)
        if hasattr(result, 'enhanced_code'):
            enhanced = str(result.enhanced_code)
        elif hasattr(result, 'code'):
            enhanced = str(result.code)
        else:
            enhanced = str(result)
        print("Enhanced code:\n")
        print(enhanced[:2000])
        output_path = "services/basiq_enhanced.py"
        with open(output_path, "w") as f:
            f.write(enhanced)
        print(f"\nSaved to: {output_path}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()