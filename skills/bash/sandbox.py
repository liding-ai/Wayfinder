"""
Bash sandbox — 受限 shell 执行

允许模型在工作目录内执行白名单命令，用于写行程文档等。
"""

DEFAULT_ALLOWED_CMD_PREFIXES = ("bash", "echo", "cat", "ls", "mkdir")
DEFAULT_TIMEOUT_SECONDS = 15

BASH_SANDBOX_ID = "bash_sandbox"


def register_bash_sandbox(
    agent,
    workdir: str,
    *,
    allowed_cmd_prefixes: tuple[str, ...] = DEFAULT_ALLOWED_CMD_PREFIXES,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> None:
    """注册 bash sandbox，限制命令前缀与工作目录。"""
    agent.action.register_bash_sandbox_action(
        expose_to_model=True,
        allowed_cmd_prefixes=list(allowed_cmd_prefixes),
        allowed_workdir_roots=[workdir],
        timeout=timeout,
    )
