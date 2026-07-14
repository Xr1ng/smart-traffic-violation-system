import json
import logging
import os
import re
import secrets
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.schemas.report import (
    ReportHistoryItem,
    ReportHistoryPage,
    ReportOut,
    SavedReportOut,
)


logger = logging.getLogger(__name__)
REPORT_ID_PATTERN = re.compile(r"^[0-9a-f]{12}$")
METADATA_HEADER = "<!-- traffic-report-meta:v1\n"
METADATA_FOOTER = "\n-->\n"
CHINA_TIMEZONE = timezone(timedelta(hours=8))


class ReportStorageError(RuntimeError):
    """A report file could not be saved or parsed."""


class ReportStorageService:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def save(self, report: ReportOut) -> SavedReportOut:
        temp_path: Path | None = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            report_id = self._new_id()
            saved = SavedReportOut(id=report_id, **report.model_dump())
            target = self.directory / self._filename(saved)
            content = self._serialize(saved)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                suffix=".tmp",
                prefix=".report-",
                dir=self.directory,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_path, target)
            return saved
        except Exception as exc:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            if isinstance(exc, ReportStorageError):
                raise
            raise ReportStorageError("历史报告保存失败") from exc

    def get(self, report_id: str) -> SavedReportOut:
        if not REPORT_ID_PATTERN.fullmatch(report_id):
            raise FileNotFoundError(report_id)
        matches = list(self.directory.glob(f"*_{report_id}.md")) if self.directory.exists() else []
        if not matches:
            raise FileNotFoundError(report_id)
        try:
            return self._read(matches[0])
        except ReportStorageError:
            raise
        except Exception as exc:
            raise ReportStorageError("历史报告文件损坏，无法读取") from exc

    def list(
        self,
        *,
        page: int,
        page_size: int,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> ReportHistoryPage:
        if not self.directory.exists():
            return ReportHistoryPage(items=[], total=0, page=page, page_size=page_size)

        reports: list[SavedReportOut] = []
        for path in self.directory.glob("*.md"):
            try:
                report = self._read(path)
            except Exception as exc:
                logger.warning("Skipping invalid report file %s: %s", path.name, exc)
                continue
            if start_time is not None and report.end_time < start_time:
                continue
            if end_time is not None and report.start_time > end_time:
                continue
            reports.append(report)

        reports.sort(key=lambda item: (item.generated_at, item.id), reverse=True)
        total = len(reports)
        offset = (page - 1) * page_size
        items = [
            ReportHistoryItem(
                id=item.id,
                title=item.title,
                start_time=item.start_time,
                end_time=item.end_time,
                generated_at=item.generated_at,
            )
            for item in reports[offset:offset + page_size]
        ]
        return ReportHistoryPage(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def _new_id(self) -> str:
        for _ in range(10):
            candidate = secrets.token_hex(6)
            if not any(self.directory.glob(f"*_{candidate}.md")):
                return candidate
        raise ReportStorageError("无法生成唯一的历史报告编号")

    @staticmethod
    def _filename(report: SavedReportOut) -> str:
        start_date = report.start_time.astimezone(CHINA_TIMEZONE).date().isoformat()
        end_date = report.end_time.astimezone(CHINA_TIMEZONE).date().isoformat()
        generated = report.generated_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{start_date}_{end_date}_{generated}_{report.id}.md"

    @staticmethod
    def _serialize(report: SavedReportOut) -> str:
        metadata = json.dumps(
            {"schema_version": 1, "report": report.model_dump(mode="json")},
            ensure_ascii=False,
            indent=2,
        )
        return f"{METADATA_HEADER}{metadata}{METADATA_FOOTER}\n{_render_markdown(report)}"

    @staticmethod
    def _read(path: Path) -> SavedReportOut:
        content = path.read_text(encoding="utf-8")
        if not content.startswith(METADATA_HEADER):
            raise ReportStorageError("历史报告文件损坏，无法读取")
        footer_index = content.find(METADATA_FOOTER, len(METADATA_HEADER))
        if footer_index < 0:
            raise ReportStorageError("历史报告文件损坏，无法读取")
        try:
            metadata = json.loads(content[len(METADATA_HEADER):footer_index])
            if metadata.get("schema_version") != 1:
                raise ValueError("unsupported schema version")
            return SavedReportOut.model_validate(metadata["report"])
        except Exception as exc:
            raise ReportStorageError("历史报告文件损坏，无法读取") from exc


def _render_markdown(report: SavedReportOut) -> str:
    snapshot = report.statistics_snapshot
    risk_items = "\n".join(f"- {item}" for item in report.risk_alerts)
    recommendation_items = "\n".join(
        f"{index}. {item}" for index, item in enumerate(report.recommendations, start=1)
    )
    type_rows = "\n".join(
        f"| {_table_text(item.name)} | {item.value} | {item.percentage}% |"
        for item in snapshot.violation_types[:5]
    )
    location_rows = "\n".join(
        f"| {_table_text(item.name or '未标注地点')} | {item.value} |"
        for item in snapshot.locations[:5]
    )
    return (
        f"# {report.title}\n\n"
        f"- 统计周期：{report.start_time.isoformat()} 至 {report.end_time.isoformat()}\n"
        f"- 生成时间：{report.generated_at.isoformat()}\n"
        f"- 生成者：{report.author}\n\n"
        f"## 01 执行摘要\n\n{report.summary}\n\n"
        f"## 02 趋势分析\n\n{report.trend_analysis}\n\n"
        f"## 03 热点分析\n\n{report.hotspot_analysis}\n\n"
        f"## 04 风险提示\n\n{risk_items or '本期未识别出明确风险提示。'}\n\n"
        f"## 05 治理建议\n\n{recommendation_items or '本期暂无补充治理建议。'}\n\n"
        "## 06 数据依据\n\n"
        f"- 违章记录：{snapshot.overview.total_violations}\n"
        f"- 案件总量：{snapshot.overview.total_cases}\n"
        f"- 审核通过率：{snapshot.overview.approve_rate}%\n"
        f"- 待审核：{snapshot.overview.pending_count}\n\n"
        "### 高发违章类型\n\n"
        "| 类型 | 数量 | 占比 |\n| --- | ---: | ---: |\n"
        f"{type_rows or '| 暂无数据 | 0 | 0% |'}\n\n"
        "### 高发地点\n\n"
        "| 地点 | 数量 |\n| --- | ---: |\n"
        f"{location_rows or '| 暂无数据 | 0 |'}\n\n"
        "---\n\n本报告由 AI 根据平台聚合统计数据生成，仅用于交通管理分析参考。\n"
    )


def _table_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
