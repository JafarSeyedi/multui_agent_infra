from __future__ import annotations

import os
import resource
import psutil


class MemoryUsageTracker:
    def current(self):
        if psutil is not None:
            process = psutil.Process()
            return process.memory_info().rss
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if os.name == 'posix':
            return int(usage * 1024)
        return int(usage)
