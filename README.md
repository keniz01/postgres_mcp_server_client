curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
-----------
uv init example
uv add ruff "mcp[cli]"
uv sync