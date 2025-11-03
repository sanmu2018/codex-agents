import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio


async def main() -> None:
    # 启动 Codex MCP 服务器（正确命令）
    async with MCPServerStdio(
        name="Codex CLI",
        params={
            "command": "npx",  # 通过 npx 启动
            "args": ["-y", "codex", "mcp-server"],  # ✅ 改这里，原来是 ["-y", "codex", "mcp"]
        },
        client_session_timeout_seconds=360000,
    ) as codex_mcp_server:
        print("✅ Codex MCP server started and connected successfully.")
        # 在这里可以添加后续逻辑，比如与 Dify 集成等
        await asyncio.sleep(1e6)  # 保持运行（防止自动退出）


if __name__ == "__main__":
    asyncio.run(main())

