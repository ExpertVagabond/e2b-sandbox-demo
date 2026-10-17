"""
E2B Code Interpreter Demo — the agent-facing SDK.

Shows how an AI agent would use E2B to safely execute generated code,
with state preserved between calls (the key differentiator).

Requires: E2B_API_KEY environment variable (free tier at e2b.dev).
Run: python demo_code_interpreter.py
"""
import os
import sys

def main():
    if not os.environ.get("E2B_API_KEY"):
        print("Set E2B_API_KEY first: export E2B_API_KEY=e2b_...")
        sys.exit(1)

    from e2b_code_interpreter import Sandbox

    print("=== E2B Code Interpreter Demo ===\n")

    with Sandbox.create() as sbx:
        print(f"Sandbox: {sbx.sandbox_id}\n")

        # 1. State persists between calls — this is the core value prop
        print("1. Stateful execution (state persists across calls):")
        sbx.run_code("data = [3, 1, 4, 1, 5, 9, 2, 6]")
        sbx.run_code("data.sort()")
        result = sbx.run_code("print(f'Sorted: {data}')")
        print(f"   {result.text}\n")

        # 2. Multi-step data analysis — typical agent workflow
        print("2. Multi-step data analysis:")
        sbx.run_code("""
import json
sales = [
    {"month": "Jan", "revenue": 12000, "units": 150},
    {"month": "Feb", "revenue": 15000, "units": 180},
    {"month": "Mar", "revenue": 11000, "units": 130},
    {"month": "Apr", "revenue": 18000, "units": 220},
    {"month": "May", "revenue": 21000, "units": 260},
]
""")
        analysis = sbx.run_code("""
total_rev = sum(r['revenue'] for r in sales)
avg_units = sum(r['units'] for r in sales) / len(sales)
best = max(sales, key=lambda r: r['revenue'])
print(f"Total revenue: ${total_rev:,}")
print(f"Avg units/month: {avg_units:.0f}")
print(f"Best month: {best['month']} (${best['revenue']:,})")
""")
        for line in analysis.text.strip().split("\n"):
            print(f"   {line}")
        print()

        # 3. Error handling — agent sees the error, sandbox stays alive
        print("3. Error handling (sandbox survives bad code):")
        bad = sbx.run_code("1 / 0")
        print(f"   Error: {bad.error.name}: {bad.error.value}")
        ok = sbx.run_code("print('Still alive after the error')")
        print(f"   {ok.text}\n")

        # 4. File generation inside the sandbox
        print("4. Generate a file (CSV) inside the sandbox:")
        sbx.run_code("""
import csv, io
buf = io.StringIO()
w = csv.writer(buf)
w.writerow(["month", "revenue"])
for r in sales:
    w.writerow([r["month"], r["revenue"]])
with open("/home/user/report.csv", "w") as f:
    f.write(buf.getvalue())
print("Wrote report.csv")
""")
        csv_content = sbx.files.read("/home/user/report.csv")
        print(f"   Downloaded from sandbox:")
        for line in csv_content.strip().split("\n"):
            print(f"     {line}")
        print()

        # 5. Install a package at runtime — agents need this
        print("5. Runtime package install (agent discovers it needs pandas):")
        sbx.run_code("import subprocess; subprocess.run(['pip', 'install', '-q', 'pandas'])")
        pandas_result = sbx.run_code("""
import pandas as pd
df = pd.DataFrame([
    {"month": r["month"], "revenue": r["revenue"], "units": r["units"]}
    for r in sales
])
print(df.describe().to_string())
""")
        for line in pandas_result.text.strip().split("\n"):
            print(f"   {line}")
        print()

    print("Sandbox auto-destroyed (context manager).")
    print("\n=== Key takeaways ===")
    print("- State persists between run_code() calls (no re-imports)")
    print("- Errors don't kill the sandbox (agent can retry)")
    print("- Files live in the sandbox filesystem (download when done)")
    print("- Packages installable at runtime (agent self-provisions)")
    print("- Context manager auto-cleanup (no leaked sandboxes)")


if __name__ == "__main__":
    main()
