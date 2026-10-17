"""
E2B Sandbox Demo — exercises the core SDK surface.

Requires: E2B_API_KEY environment variable (free tier at e2b.dev).
Run: python demo_sandbox.py
"""
import os
import sys
import time

def main():
    if not os.environ.get("E2B_API_KEY"):
        print("Set E2B_API_KEY first: export E2B_API_KEY=e2b_...")
        sys.exit(1)

    from e2b import Sandbox

    print("=== E2B Sandbox Demo ===\n")

    # 1. Create a sandbox
    print("1. Creating sandbox...")
    t0 = time.time()
    sbx = Sandbox.create()
    cold_start = time.time() - t0
    print(f"   Sandbox ID: {sbx.sandbox_id}")
    print(f"   Cold start: {cold_start:.2f}s\n")

    # 2. Run a shell command
    print("2. Running shell command...")
    result = sbx.commands.run('echo "Hello from E2B sandbox"')
    print(f"   stdout: {result.stdout.strip()}")
    print(f"   exit code: {result.exit_code}\n")

    # 3. Check the environment
    print("3. Sandbox environment:")
    info = sbx.commands.run("uname -a && python3 --version && node --version 2>/dev/null || true")
    for line in info.stdout.strip().split("\n"):
        print(f"   {line}")
    print()

    # 4. Write a file into the sandbox
    print("4. Writing a file...")
    sbx.files.write("/home/user/hello.txt", "Built on E2B this week.\n")
    content = sbx.files.read("/home/user/hello.txt")
    print(f"   Read back: {content.strip()}\n")

    # 5. Install a package and use it
    print("5. Installing a pip package inside the sandbox...")
    install = sbx.commands.run("pip install httpx 2>&1 | tail -1")
    print(f"   {install.stdout.strip()}")

    script = """
import httpx, json
r = httpx.get("https://httpbin.org/ip")
print(json.dumps(r.json(), indent=2))
"""
    sbx.files.write("/home/user/fetch.py", script)
    run = sbx.commands.run("python3 /home/user/fetch.py")
    print(f"   Sandbox IP (not yours):\n   {run.stdout.strip()}\n")

    # 6. Demonstrate isolation — the sandbox can't see our filesystem
    print("6. Isolation check:")
    check = sbx.commands.run("ls /Users 2>&1 || echo 'No /Users — isolated'")
    print(f"   {check.stdout.strip()}\n")

    # 7. Measure command latency
    print("7. Command latency:")
    t0 = time.time()
    sbx.commands.run("true")
    latency = (time.time() - t0) * 1000
    print(f"   No-op command: {latency:.0f}ms\n")

    # 8. Kill the sandbox
    print("8. Killing sandbox...")
    sbx.kill()
    print("   Done. Sandbox destroyed.\n")

    print("=== Summary ===")
    print(f"Cold start: {cold_start:.2f}s")
    print(f"Command latency: {latency:.0f}ms")
    print("Sandbox created, used, and destroyed — no state leaks.")


if __name__ == "__main__":
    main()
