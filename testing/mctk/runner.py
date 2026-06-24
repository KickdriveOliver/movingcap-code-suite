"""Tiny test runner for MovingCap functional tests (host-side CPython).

``TestRunner`` provides the small amount of structure a functional test needs:
labelled sections, pass/fail assertions, a printed summary, and a JSON report
written to a ``results/`` directory. It deliberately stays dependency-free so it
runs anywhere CPython 3 does and is easy to drop into CI.

Example::

    from mctk import TestRunner
    t = TestRunner("driveTurntablePositioning", device_ip="192.168.2.150")
    t.section("Startup")
    t.check("script started", monitor.has_line("started"))
    ok = t.finish(results_dir="results")
    raise SystemExit(0 if ok else 1)
"""

import datetime
import json
import os

PASS = "[PASS]"
FAIL = "[FAIL]"


class TestRunner:
    def __init__(self, name, device_ip=None, script=None):
        self.name = name
        self.device_ip = device_ip
        self.script = script
        self.results = []
        self.started_at = datetime.datetime.now()

    def section(self, title):
        print("\n" + "=" * 60)
        print("  " + title)
        print("=" * 60)

    def check(self, name, condition, detail=""):
        """Record a pass/fail assertion. Returns the boolean condition."""
        condition = bool(condition)
        status = PASS if condition else FAIL
        line = status + " " + name
        if detail:
            line += " | " + detail
        print(line)
        self.results.append({"name": name, "passed": condition, "detail": detail})
        return condition

    @property
    def passed(self):
        return sum(1 for r in self.results if r["passed"])

    @property
    def total(self):
        return len(self.results)

    @property
    def success(self):
        return self.total > 0 and self.passed == self.total

    def summary(self):
        self.section("Summary")
        print("Results: " + str(self.passed) + "/" + str(self.total) + " checks passed")
        for r in self.results:
            status = PASS if r["passed"] else FAIL
            line = "  " + status + " " + r["name"]
            if r["detail"]:
                line += " | " + r["detail"]
            print(line)

    def write_report(self, results_dir="results"):
        """Write a JSON report and return its path."""
        os.makedirs(results_dir, exist_ok=True)
        stamp = datetime.datetime.now()
        filename = self.name + "-" + stamp.strftime("%Y%m%d-%H%M%S") + ".json"
        path = os.path.join(results_dir, filename)
        report = {
            "test_suite": self.name,
            "timestamp": stamp.isoformat(),
            "device_ip": self.device_ip,
            "script": self.script,
            "passed": self.passed,
            "total": self.total,
            "success": self.success,
            "results": self.results,
        }
        with open(path, "w") as handle:
            json.dump(report, handle, indent=2)
        print("JSON report: " + path)
        return path

    def finish(self, results_dir="results"):
        """Print the summary, write the report, and return ``self.success``."""
        self.summary()
        self.write_report(results_dir)
        return self.success
