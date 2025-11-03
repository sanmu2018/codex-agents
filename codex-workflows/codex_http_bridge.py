import subprocess
import json
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/run")
async def run_tool(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    if not prompt:
        return {"error": "Missing 'prompt' field."}

    try:
        cmd = ["codex", "exec", prompt]
        print("🚀 Running:", " ".join(cmd))

        # 使用 Popen 实时输出
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        stdout_lines = []
        stderr_lines = []

        # 实时读取输出流
        for line in process.stdout:
            print(f"[STDOUT] {line}", end="")
            stdout_lines.append(line)
        for line in process.stderr:
            print(f"[STDERR] {line}", end="")
            stderr_lines.append(line)

        process.wait(timeout=120)

        return {
            "prompt": prompt,
            "stdout": "".join(stdout_lines).strip(),
            "stderr": "".join(stderr_lines).strip(),
            "returncode": process.returncode
        }

    except subprocess.TimeoutExpired:
        process.kill()
        return {"error": "Codex execution timed out after 120 seconds"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

