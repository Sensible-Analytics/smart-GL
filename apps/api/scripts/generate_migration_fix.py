import os
import dspy
import asyncio
import re

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    dspy.configure(lm=dspy.LM("groq/llama-3.1-8b-instant", api_key=GROQ_API_KEY))
else:
    print("ERROR: No GROQ_API_KEY")
    exit(1)

MIGRATION_CONTEXT = """
FIX SUPABASE MIGRATION ERROR: uuid_generate_v4() does not exist

RESEARCH FINDINGS:
- Supabase hosted projects have uuid-ossp enabled by default
- Supabase CLI has a bug where uuid-ossp isn't enabled during db push
- Bug tracked in: github.com/supabase/supabase/issues/39125
- Fix: Add "CREATE EXTENSION IF NOT EXISTS uuid-ossp;" as FIRST LINE in migration
- Alternative: Use gen_random_uuid() (native Postgres 17+, recommended for portability)

FILES TO FIX:
- infra/supabase/migrations/001_extensions.sql - ADD uuid-ossp as first line
- infra/supabase/migrations/002_tenants.sql - Replace uuid_generate_v4()
- infra/supabase/migrations/003_accounts.sql - Replace uuid_generate_v4()  
- infra/supabase/migrations/004_bank_feeds.sql - Replace uuid_generate_v4()
- infra/supabase/migrations/005_categorisations.sql - Replace uuid_generate_v4()
- infra/supabase/migrations/006_journal.sql - Replace uuid_generate_v4()
- infra/supabase/migrations/010_demo_accounts.sql - Replace uuid_generate_v4()

SCRIPT SHOULD:
1. Ensure 001_extensions.sql has uuid-ossp as first line: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
2. Replace ALL uuid_generate_v4() with gen_random_uuid()
3. Write files back
4. Print confirmation
"""


class MigrationFixer(dspy.Signature):
    context: str = dspy.InputField(desc="Migration context with problem and files")
    fix_script: dspy.Code["python"] = dspy.OutputField(desc="Python script to fix migrations in place")


async def main():
    fixer = dspy.Predict(MigrationFixer)
    
    print("=" * 60)
    print("DSPY - Migration Fix Generator")
    print("=" * 60)
    
    result = fixer(context=MIGRATION_CONTEXT)
    code = str(result.fix_script)
    
    print(f"\nGenerated fix script:\n{code[:2000]}")
    
    script_path = "/tmp/fix_migrations.py"
    with open(script_path, "w") as f:
        f.write(code)
    
    print(f"\nSaved to: {script_path}")
    print("\nExecuting fix...")
    
    exec(compile(code, script_path, "exec"))
    
    print("\nMigrations fixed!")
    print("Next: Run supabase db push")


if __name__ == "__main__":
    asyncio.run(main())