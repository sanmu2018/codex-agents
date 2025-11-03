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
        # 直接调用 Codex CLI 处理请求
        cmd = ["codex", "exec", prompt]
        print("🚀 Running:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        return {
            "prompt": prompt,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

