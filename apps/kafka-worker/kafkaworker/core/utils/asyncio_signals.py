import asyncio
import signal
from collections.abc import Awaitable, Callable
from typing import Optional


async def wait_for_shutdown_signal(
    on_shutdown: Optional[Callable[[], Awaitable[None] | None]] = None,
) -> None:
    """Block until SIGTERM or SIGINT, optionally running an async shutdown hook."""
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_signal() -> None:
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_signal)

    await stop_event.wait()

    if on_shutdown is not None:
        result = on_shutdown()
        if asyncio.iscoroutine(result):
            await result
