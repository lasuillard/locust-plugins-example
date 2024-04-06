import re

import locust_plugins  # noqa: F401
from locust import task
from opentelemetry import trace

from load_testing.helpers.otel import init_otel
from load_testing.users.tcp import TCPUser as _TCPUser

YES_OR_NO = re.compile(b"(yes|no)")

init_otel()

tracer = trace.get_tracer("locust")


class TCPUser(_TCPUser):  # noqa: D101
    record = True

    @task
    def hello(self) -> None:  # noqa: D102
        self.send_bytes_rec(
            b"hello",
            expect=b"world",
        )

    @task
    def loud_speaker(self) -> None:  # noqa: D102
        with tracer.start_as_current_span("loud_speaker"):
            with tracer.start_as_current_span("hello"):
                self.send_bytes_rec(b"hello", expect=b"world")
            with tracer.start_as_current_span("get yes"):
                self.send_bytes_rec(b"get yes", expect=b"yes")
            with tracer.start_as_current_span("bye"):
                self.send_bytes_rec(b"bye", expect=b"default response")
