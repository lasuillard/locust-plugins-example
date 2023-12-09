import inspect
import re
import socket
from collections.abc import Callable, Mapping
from typing import Any, cast
from urllib.parse import urlparse

from locust import User

from load_testing.helpers.locust import Recorder


class TCPUser(User):
    """Abstract Locust user for TCP."""

    abstract = True

    host = "tcp://127.0.0.1:8888"
    buff_size = 4096

    record = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401, D107; arguments controlled by Locust
        super().__init__(*args, **kwargs)

        url = urlparse(self.host)
        self._client_defaults = {
            "args": (),
            "kwargs": {
                "host": url.hostname,
                "port": url.port,
                "buff_size": self.buff_size,
            },
        }

    def get_client(self, *args: Any, **kwargs: Any) -> "Client":  # noqa: ANN401
        """Get a TCP client.

        Returns:
            `Client`: TCP client instance.
        """
        return Client(
            *(args or self._client_defaults["args"]),
            **(cast(Mapping, self._client_defaults["kwargs"]) | kwargs),
        )

    def send_bytes_rec(
        self,
        data: bytes,
        *,
        expect: bytes | re.Pattern[bytes] | Callable[[bytes], bool] | None = None,
    ) -> bytes:
        """Send and receive bytes with recorded.

        Args:
            data (`bytes`): Bytes to send.
            expect (`bytes | re.Pattern[bytes] | Callable[[bytes], bool]`, optional): Assertion schemes to check result. If `None`, skip checks. Defaults to `None`.

        Raises:
            TypeError: Raised for unsupported assertion schemes.

        Returns:
            `bytes`: Received bytes.
        """  # noqa: E501
        with Recorder(
            enabled=self.record,
            request_type="tcp",
            request_name=inspect.stack()[1].function,
            environment=self.environment,
        ) as recorder:
            result = self.get_client().send_bytes(data)

            # TODO(lasuillard): Define custom error class as assertion statements will be wiped out by optimization
            if isinstance(expect, bytes):
                assert result == expect, f"Received {result!r} while expecting {expect!r}"  # noqa: S101
            elif isinstance(expect, re.Pattern):
                assert (  # noqa: S101
                    expect.match(result) is not None
                ), f"Result {result!r} does not match to given pattern {expect!r}"
            elif callable(expect):
                # NOTE: Assumes given callable complies to the expected signature without checking it actually
                assert expect(  # noqa: S101
                    result,
                ), f"Result {result!r} did not pass the provided check function {expect!r}"
            elif expect is None:
                pass
            else:
                msg = f"Unexpected type '{type(expect).__name__}' for `expect`"
                raise TypeError(msg)

            recorder.set_response(result, response_length_bytes=len(result))
            return result


class Client:
    """TCP Client class for wrapping `socket.socket` with extra functionalities."""

    def __init__(self, host: str, port: int, buff_size: int) -> None:
        """Initialize client instance.

        Args:
            host (`str`): Host TCP address to connect
            port (`int`): Number of host port.
            buff_size (`int`): Size of buffer.
        """
        self._host = host
        self._port = port
        self._buff_size = buff_size

    def send_bytes(self, data: bytes) -> bytes:
        """Send data and return received full data."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self._host, self._port))
            sock.sendall(data)

            return _recvall(sock, buff_size=self._buff_size)


def _recvall(sock: socket.socket, buff_size: int = 4096) -> bytes:
    """Receive all bytes from socket."""
    data = b""
    while True:
        part = sock.recv(buff_size)
        data += part
        if len(part) < buff_size:
            break

    return data
