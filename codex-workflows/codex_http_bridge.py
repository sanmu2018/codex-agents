import asyncio
import contextlib
import json
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()

@app.post("/run")
async def run_tool(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    if not prompt:
        return {"error": "Missing 'prompt' field."}

    cmd = ["codex", "exec", prompt]
    print("🚀 Running:", " ".join(cmd))

    async def stream_process() -> AsyncGenerator[str, None]:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024
            )
        except Exception as exc:  # 捕获创建进程失败
            error_payload = {"error": str(exc)}
            yield json.dumps(error_payload, ensure_ascii=False) + "\n"
            return

        queue: asyncio.Queue = asyncio.Queue()

        async def forward_stream(stream: asyncio.StreamReader | None, name: str) -> None:
            if stream is None:
                await queue.put((name, None))
                return
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace").rstrip("\n")
                    print(f"[{name.upper()}] {decoded}")
                    await queue.put((name, decoded))
            finally:
                await queue.put((name, None))

        readers = [
            asyncio.create_task(forward_stream(process.stdout, "stdout")),
            asyncio.create_task(forward_stream(process.stderr, "stderr")),
        ]

        finished_streams = 0
        try:
            while finished_streams < len(readers):
                name, payload = await queue.get()
                if payload is None:
                    finished_streams += 1
                    continue
                yield json.dumps({"stream": name, "data": payload}, ensure_ascii=False) + "\n"

            try:
                returncode = await asyncio.wait_for(process.wait(), timeout=120)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                timeout_payload = {"error": "Codex execution timed out after 120 seconds"}
                yield json.dumps(timeout_payload, ensure_ascii=False) + "\n"
                return

            yield json.dumps({"returncode": returncode}, ensure_ascii=False) + "\n"
        finally:
            for reader in readers:
                if not reader.done():
                    reader.cancel()
                    with contextlib.suppress(Exception):
                        await reader

    return StreamingResponse(stream_process(), media_type="application/jsonl")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

