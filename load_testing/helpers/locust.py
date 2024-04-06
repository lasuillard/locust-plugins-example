import inspect
import time
from types import TracebackType
from typing import Any, Self

from greenlet import GreenletExit
from locust.env import Environment
from opentelemetry import trace


class Recorder:
    """Context manager recording response for Locust."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        request_type: str = "notset",
        request_name: str | None = None,
        environment: Environment,
    ) -> None:
        """Initialize a recorder.

        Args:
            environment (`locust.env.Environment`): Locust runner environment.
            enabled (`bool`, optional): Whether to enable recorder. If set `False`, skip sending record. Defaults to True.
            request_type (`str`, optional): Type of request. Defaults to `"notset"`.
            request_name (`str`, optional): Name of request. If `None`, use caller's name (from stack frame). Defaults to `None`.
        """  # noqa: E501
        self.request_name = request_name or inspect.stack()[1].function
        self.environment = environment

        self._enabled = enabled
        self._request_meta: dict[str, Any] = {
            "name": self.request_name,
            "request_type": request_type,
            "response": None,
            "response_length": 0,
            "exception": None,
            "context": {},  # BUG: Required for locust-plugins timescale DB handler
        }
        self._start_time: float | None = None

    def set_response(self, response: Any, *, response_length_bytes: int | None = None) -> None:  # noqa: ANN401
        """Set record's response.

        Args:
            response (`Any`): Response from request.
            response_length_bytes (`int`, optional): Length of response in bytes. If `None`, record 0. Defaults to `None`.
        """  # noqa: E501
        self._request_meta["response"] = response
        if response_length_bytes is not None:
            self._request_meta["response_length"] = response_length_bytes

        self._request_meta["response_time"] = self._get_elapsed_ms()

    def _get_elapsed_ms(self) -> float:
        if self._start_time is None:
            msg = "`._start_time` is `None`, seems recorder hasn't started yet"
            raise ValueError(msg)

        return 1_000 * (time.time() - self._start_time)

    def __enter__(self) -> Self:
        self._start_time = time.time()
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc_val: Exception | None,
        _traceback: TracebackType | None,
    ) -> bool | None:
        # Do not bother Locust
        if exc_type is GreenletExit:
            return None

        span = trace.get_current_span()

        self._request_meta["start_time"] = self._start_time
        if exc_val is None:
            # No exception occurred; should use `.set_response(...)` method to set response for report
            pass
        else:
            self._request_meta["exception"] = exc_val
            span.record_exception(exc_val)
            span.set_status(trace.Status(trace.StatusCode.ERROR, description=str(exc_val)))

        self._request_meta.setdefault("response_time", self._get_elapsed_ms())

        # Add trace info to context
        if span.is_recording():
            span_ctx = span.get_span_context()
            self._request_meta["context"].update(
                {
                    "trace_id": f"{span_ctx.trace_id:x}",
                    "span_id": f"{span_ctx.span_id:x}",
                },
            )

        if self._enabled:
            self.environment.events.request.fire(**self._request_meta)

        return True
