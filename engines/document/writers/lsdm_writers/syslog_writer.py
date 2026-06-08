from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import Any

from engines.document.models.lsdm_models import EventLogDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions

FACILITY_CODES = {
    "kern": 0, "user": 1, "mail": 2, "daemon": 3, "auth": 4,
    "syslog": 5, "lpr": 6, "news": 7, "uucp": 8, "cron": 9,
    "authpriv": 10, "ftp": 11, "local0": 16, "local1": 17,
    "local2": 18, "local3": 19, "local4": 20, "local5": 21,
    "local6": 22, "local7": 23,
}

SEVERITY_CODES = {
    "emerg": 0, "alert": 1, "crit": 2, "err": 3,
    "warning": 4, "notice": 5, "info": 6, "debug": 7,
}


class SyslogWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: EventLogDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: EventLogDocument) -> bytes:
        lines: list[str] = []
        for event in document.events:
            facility_code = FACILITY_CODES.get(event.syslog_facility.value if event.syslog_facility else "", 1)
            severity_code = SEVERITY_CODES.get(event.syslog_severity.value if event.syslog_severity else "", 6)
            pri = facility_code * 8 + severity_code
            ts = event.timestamp or datetime.now()
            ts_str = ts.isoformat()
            hostname = event.syslog_hostname or "-"
            app_name = event.syslog_app_name or "-"
            proc_id = event.syslog_proc_id or "-"
            msg_id = event.syslog_msg_id or "-"
            sd_text = "-"
            if event.syslog_structured_data:
                sd_parts: list[str] = []
                for sd in event.syslog_structured_data:
                    params = " ".join(f'{k}="{v}"' for k, v in sd.parameters.items())
                    sd_parts.append(f"[{sd.sd_id} {params}]" if params else f"[{sd.sd_id}]")
                sd_text = " ".join(sd_parts)
            message = event.syslog_message or event.raw or ""
            lines.append(
                f"<{pri}>1 {ts_str} {hostname} {app_name} {proc_id} {msg_id} {sd_text} {message}"
            )
        return "\n".join(lines).encode("utf-8")

    async def write_to_file(self, document: EventLogDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-syslog"]

    def get_supported_extensions(self) -> list[str]:
        return [".syslog"]
