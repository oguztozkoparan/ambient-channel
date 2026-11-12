"""Progress display for long steps: in-place bar on a terminal, one line per 10% otherwise."""

import sys
import time

WIDTH = 30


class Progress:
    def __init__(self, label: str) -> None:
        self.label = label
        self.started = time.monotonic()
        self.decile = -1

    def update(self, fraction: float) -> None:
        f = min(max(fraction, 0.0), 1.0)
        text = f"{self.label:<18} [{'#' * round(f * WIDTH):<{WIDTH}}] {f:4.0%}"
        if sys.stderr.isatty():
            left = ""
            if 0.02 < f < 1:  # too early to estimate below 2%
                secs = int((time.monotonic() - self.started) * (1 - f) / f)
                left = f"{secs // 60}m{secs % 60:02d}s left"
            sys.stderr.write(f"\r{text}  {left:<12}")
            sys.stderr.flush()
        elif int(f * 10) > self.decile:  # logs and agents: no carriage returns
            self.decile = int(f * 10)
            print(text, file=sys.stderr)

    def done(self) -> None:
        self.update(1.0)
        if sys.stderr.isatty():
            sys.stderr.write(f"  {time.monotonic() - self.started:.0f}s\n")
