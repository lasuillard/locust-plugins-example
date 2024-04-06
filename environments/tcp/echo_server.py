#!/usr/bin/env python3
# Ref: https://github.com/Ypurek/TCP-Locust
import argparse
import logging
import logging.config
import random
import socket
import time

BUFFER_SIZE = 4096

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "formatter": "simple",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": "DEBUG",
            "formatter": "simple",
            "class": "logging.FileHandler",
            "filename": "./tcp_echo_server.log",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG",
        "propagate": False,
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)


def main(*, host: str, port: int, mock_duration: float) -> None:
    """Run TCP server."""
    session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    session.bind((host, port))
    session.listen(10)

    logger.info("Server started")

    while True:
        sock, _address = session.accept()
        data = _recvall(sock, BUFFER_SIZE)

        # Sleep for 0. ~ 0.2 seconds before response
        time.sleep(mock_duration * random.random())  # noqa: S311

        response = b"default response"
        match data.lower():
            case b"hello":
                response = b"world"
            case b"get yes":
                response = random.choice((b"yes", b"no"))  # noqa: S311

        logger.debug("Received %r, replying with %r", data, response)
        sock.sendall(response)
        sock.close()


def _recvall(sock: socket.socket, buff_size: int) -> bytes:
    """Receive all bytes from socket."""
    data = b""
    while True:
        part = sock.recv(buff_size)
        data += part
        if len(part) < buff_size:
            break

    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="", description="Simple TCP server for tests")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to listen for")  # noqa: S104
    parser.add_argument("--port", type=int, default=8888, help="Port to bind")
    parser.add_argument(
        "--mock-duration",
        type=float,
        default=0.2,
        help="Maximum of mock duration to wait before send response back to client",
    )
    args = parser.parse_args()

    if args.mock_duration <= 0:
        msg = "Mock duration should be bigger than 0"
        raise ValueError(msg)

    main(host=args.host, port=args.port, mock_duration=args.mock_duration)
