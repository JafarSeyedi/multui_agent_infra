from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from engines.document.models.lsdm_models import (
    CefSeverity,
    EventLogDocument,
    LogEvent,
    LogSource,
    SyslogFacility,
    SyslogSeverity,
    SyslogStructuredData,
)
from engines.document.models.media_types import MediaType, MEDIA_TYPES
from engines.document.models.standard import DocumentStandard
from ..base import BaseDocumentParser, ParseOptions

SYSLOG_PATTERN = re.compile(
    r"<(?P<pri>\d{1,3})>"
    r"(?P<timestamp>\S+)\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?P<app_name>\S+)(?:\[(?P<proc_id>\d+)\])?"
    r":\s*(?P<message>.*)"
)

RFC5424_PATTERN = re.compile(
    r"<(?P<pri>\d{1,3})>(?P<version>\d)\s+"
    r"(?P<timestamp>\S+)\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?P<app_name>\S+)\s+"
    r"(?P<proc_id>\S+)\s+"
    r"(?P<msg_id>\S+)\s+"
    r"(?P<structured_data>\[.*\]|-)\s*"
    r"(?P<message>.*)"
)


class SyslogParser(BaseDocumentParser):
    name = "syslog_parser"
    supported_extensions = [".syslog"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> EventLogDocument:
        text = data.decode("utf-8")
        events: list[LogEvent] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            event = self._parse_line(line)
            if event:
                events.append(event)
        return EventLogDocument(
            document_id=document_id,
            title="",
            kind=DocumentStandard.LSDM,
            source=LogSource.SYSLOG,
            events=events,
            media_type=cast(MediaType, MEDIA_TYPES.get("syslog")),
        )

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> EventLogDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> EventLogDocument:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def _parse_line(self, line: str) -> LogEvent | None:
        match = RFC5424_PATTERN.match(line)
        if not match:
            match = SYSLOG_PATTERN.match(line)
        if not match:
            return LogEvent(
                source=LogSource.SYSLOG,
                attributes=[],
                raw=line,
            )
        pri = int(match.group("pri"))
        facility_code = pri // 8
        severity_code = pri % 8
        facility_map = {
            0: SyslogFacility.KERN, 1: SyslogFacility.USER, 2: SyslogFacility.MAIL,
            3: SyslogFacility.DAEMON, 4: SyslogFacility.AUTH, 5: SyslogFacility.SYSLOG,
            6: SyslogFacility.LPR, 7: SyslogFacility.NEWS, 8: SyslogFacility.UUCP,
            9: SyslogFacility.CRON, 10: SyslogFacility.AUTHPRIV, 11: SyslogFacility.FTP,
            16: SyslogFacility.LOCAL0, 17: SyslogFacility.LOCAL1, 18: SyslogFacility.LOCAL2,
            19: SyslogFacility.LOCAL3, 20: SyslogFacility.LOCAL4, 21: SyslogFacility.LOCAL5,
            22: SyslogFacility.LOCAL6, 23: SyslogFacility.LOCAL7,
        }
        severity_map = {
            0: SyslogSeverity.EMERG, 1: SyslogSeverity.ALERT, 2: SyslogSeverity.CRIT,
            3: SyslogSeverity.ERR, 4: SyslogSeverity.WARNING, 5: SyslogSeverity.NOTICE,
            6: SyslogSeverity.INFO, 7: SyslogSeverity.DEBUG,
        }
        facility = facility_map.get(facility_code)
        severity = severity_map.get(severity_code)
        ts_str = match.group("timestamp")
        timestamp: datetime | None = None
        try:
            timestamp = datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            pass
        structured_data: list[SyslogStructuredData] = []
        if "structured_data" in match.groupdict():
            sd_text = match.group("structured_data")
            if sd_text and sd_text != "-":
                sd_blocks = re.findall(r"\[(.*?)\]", sd_text)
                for block in sd_blocks:
                    parts = block.split()
                    if parts:
                        sd_id = parts[0]
                        params = {}
                        for param in parts[1:]:
                            if "=" in param:
                                k, v = param.split("=", 1)
                                params[k] = v.strip('"')
                        structured_data.append(SyslogStructuredData(sd_id=sd_id, parameters=params))
        return LogEvent(
            source=LogSource.SYSLOG,
            timestamp=timestamp,
            syslog_facility=facility,
            syslog_severity=severity,
            syslog_hostname=match.group("hostname"),
            syslog_app_name=match.group("app_name"),
            syslog_proc_id=match.group("proc_id") if "proc_id" in match.groupdict() else None,
            syslog_msg_id=match.group("msg_id") if "msg_id" in match.groupdict() else None,
            syslog_message=match.group("message"),
            syslog_structured_data=structured_data,
            raw=line,
        )
