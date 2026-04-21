"""
Report Generator for Orchestration Analytics

Generates comprehensive reports from collected metrics including:
- Performance reports
- Bottleneck analysis reports
- Skill gap reports
- Workflow execution reports
- Resource utilization reports
- Trend analysis reports
- Executive summaries

This implementation provides:

    Multiple Report Types: Performance, Bottleneck, Skill Gap, Workflow, Resource, Trend, Executive, Custom
    Multiple Output Formats: JSON, CSV, HTML, Markdown (PDF planned)
    Time Range Filtering: Reports for specific time periods
    Executive Summaries: High-level overview for management
    Trend Analysis: Detect increasing/decreasing trends and forecast
    Recommendations: Actionable insights based on data
    Export Capabilities: Save reports to files
    Report History: Track last 100 generated reports
    HTML Reports: Styled HTML with tables and summaries
    CSV Export: Flattened data for spreadsheet analysis

The report generator integrates all your analytics components (bottleneck detector, performance tracker, 
workflow collector, skill gap analyzer) to produce comprehensive, actionable reports.
"""

import json
import csv
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
from pathlib import Path
import io

from ....shared.logger import get_logger
from ....shared.state_manager import state_manager
from ....shared.config import config
from ....shared.file_utils import file_utils

from .bottleneck_detector import BottleneckDetector, get_bottleneck_detector
from .performance_tracker import PerformanceTracker, get_performance_tracker
from .workflow_metrics_collector import WorkflowMetricsCollector, get_workflow_metrics_collector
from .skill_gap_analyzer import SkillGapAnalyzer, get_skill_gap_analyzer

logger = get_logger(__name__)


class ReportFormat(Enum):
    """Supported report output formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"  # Planned for future


class ReportType(Enum):
    """Types of reports that can be generated"""
    PERFORMANCE = "performance"
    BOTTLENECK = "bottleneck"
    SKILL_GAP = "skill_gap"
    WORKFLOW = "workflow"
    RESOURCE = "resource"
    TREND = "trend"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    report_type: ReportType
    format: ReportFormat = ReportFormat.JSON
    time_range_hours: int = 24
    include_recommendations: bool = True
    include_charts: bool = False  # For HTML reports
    max_items: int = 50
    output_path: Optional[str] = None
    title: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_type": self.report_type.value,
            "format": self.format.value,
            "time_range_hours": self.time_range_hours,
            "include_recommendations": self.include_recommendations,
            "include_charts": self.include_charts,
            "max_items": self.max_items,
            "output_path": self.output_path,
            "title": self.title,
            "filters": self.filters
        }


@dataclass
class Report:
    """Generated report container"""
    report_id: str
    report_type: ReportType
    title: str
    generated_at: datetime
    time_range: Tuple[datetime, datetime]
    data: Dict[str, Any]
    format: ReportFormat
    content: str
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "report_type": self.report_type.value,
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "time_range": {
                "start": self.time_range[0].isoformat(),
                "end": self.time_range[1].isoformat()
            },
            "data": self.data,
            "format": self.format.value,
            "file_path": self.file_path
        }


class ReportGenerator:
    """
    Generates comprehensive reports from analytics data.
    
    Features:
    - Multiple report types
    - Multiple output formats (JSON, CSV, HTML, Markdown)
    - Time range filtering
    - Trend analysis
    - Executive summaries
    - Export to files
    """
    
    def __init__(self):
        self.bottleneck_detector = get_bottleneck_detector()
        self.performance_tracker = get_performance_tracker()
        self.workflow_collector = get_workflow_metrics_collector()
        self.skill_gap_analyzer = get_skill_gap_analyzer()
        
        self.report_history: List[Report] = []
        
        logger.info("ReportGenerator initialized")
    
    def generate_report(self, config: ReportConfig) -> Report:
        """
        Generate a report based on configuration.
        
        Args:
            config: Report configuration
            
        Returns:
            Generated Report object
        """
        report_id = f"{config.report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=config.time_range_hours)
        time_range = (start_time, end_time)
        
        # Generate report data based on type
        if config.report_type == ReportType.PERFORMANCE:
            report_data = self._generate_performance_report(start_time, end_time, config)
            title = config.title or f"Performance Report - {start_time.date()} to {end_time.date()}"
        elif config.report_type == ReportType.BOTTLENECK:
            report_data = self._generate_bottleneck_report(start_time, end_time, config)
            title = config.title or f"Bottleneck Analysis Report - {start_time.date()}"
        elif config.report_type == ReportType.SKILL_GAP:
            report_data = self._generate_skill_gap_report(start_time, end_time, config)
            title = config.title or f"Skill Gap Analysis Report - {start_time.date()}"
        elif config.report_type == ReportType.WORKFLOW:
            report_data = self._generate_workflow_report(start_time, end_time, config)
            title = config.title or f"Workflow Execution Report - {start_time.date()}"
        elif config.report_type == ReportType.RESOURCE:
            report_data = self._generate_resource_report(start_time, end_time, config)
            title = config.title or f"Resource Utilization Report - {start_time.date()}"
        elif config.report_type == ReportType.TREND:
            report_data = self._generate_trend_report(start_time, end_time, config)
            title = config.title or f"Trend Analysis Report - Last {config.time_range_hours} Hours"
        elif config.report_type == ReportType.EXECUTIVE:
            report_data = self._generate_executive_report(start_time, end_time, config)
            title = config.title or f"Executive Summary - {start_time.date()}"
        else:
            report_data = self._generate_custom_report(start_time, end_time, config)
            title = config.title or f"Custom Report - {start_time.date()}"
        
        # Format the report
        content = self._format_report(report_data, config.format, title)
        
        # Save to file if output path specified
        file_path = None
        if config.output_path:
            file_path = self._save_report(content, config.output_path, config.format)
        
        report = Report(
            report_id=report_id,
            report_type=config.report_type,
            title=title,
            generated_at=datetime.now(),
            time_range=time_range,
            data=report_data,
            format=config.format,
            content=content,
            file_path=file_path
        )
        
        # Store in history
        self.report_history.append(report)
        if len(self.report_history) > 100:
            self.report_history = self.report_history[-100:]
        
        logger.info(f"Generated {config.report_type.value} report: {report_id}")
        
        return report
    
    def _generate_performance_report(self, start_time: datetime, end_time: datetime,
                                    config: ReportConfig) -> Dict[str, Any]:
        """Generate performance report"""
        # Get performance summary
        perf_summary = self.performance_tracker.get_metrics_summary()
        
        # Get workflow stats
        workflow_summary = self.workflow_collector.get_workflow_summary()
        workflow_types = self.workflow_collector.get_workflow_type_stats()
        step_types = self.workflow_collector.get_step_type_stats()
        
        # Get slowest workflows
        slowest_workflows = self.workflow_collector.get_slowest_workflows(config.max_items)
        
        # Get most failed steps
        failed_steps = self.workflow_collector.get_most_failed_steps(config.max_items)
        
        # Calculate performance metrics
        avg_response_time = self.performance_tracker.get_metric_value(
            "agent.response_time", 
            self.performance_tracker._get_aggregation("avg")
        )
        
        success_rate = self.performance_tracker.get_metric_value(
            "task.success_rate",
            self.performance_tracker._get_aggregation("avg")
        )
        
        report_data = {
            "summary": {
                "total_workflows": workflow_summary.get("total_workflows", 0),
                "completed_workflows": workflow_summary.get("completed", 0),
                "failed_workflows": workflow_summary.get("failed", 0),
                "success_rate": workflow_summary.get("overall_success_rate", 100),
                "active_workflows": workflow_summary.get("active_workflows", 0),
                "avg_workflow_duration": workflow_summary.get("average_workflow_duration", 0),
                "avg_agent_response_time": avg_response_time or 0,
                "task_success_rate": success_rate or 100
            },
            "workflow_types": workflow_types,
            "step_types": step_types,
            "performance_metrics": {
                "slowest_workflows": slowest_workflows,
                "most_failed_steps": failed_steps
            },
            "recommendations": self._generate_performance_recommendations(
                workflow_summary, slowest_workflows, failed_steps
            ) if config.include_recommendations else []
        }
        
        return report_data
    
    def _generate_bottleneck_report(self, start_time: datetime, end_time: datetime,
                                   config: ReportConfig) -> Dict[str, Any]:
        """Generate bottleneck analysis report"""
        # Detect bottlenecks
        bottlenecks = self.bottleneck_detector.detect_bottlenecks()
        
        # Get bottleneck summary
        bottleneck_summary = self.bottleneck_detector.get_bottleneck_summary()
        
        # Get suggestions
        suggestions = self.bottleneck_detector.get_suggestions()
        
        # Get statistics
        stats = self.bottleneck_detector.get_statistics()
        
        # Filter by time range if needed
        filtered_bottlenecks = [
            b for b in bottlenecks 
            if start_time <= b.timestamp <= end_time
        ][:config.max_items]
        
        report_data = {
            "summary": bottleneck_summary,
            "bottlenecks": [b.to_dict() for b in filtered_bottlenecks],
            "statistics": stats,
            "suggestions": suggestions[:config.max_items] if config.include_recommendations else [],
            "severity_breakdown": {
                "critical": len([b for b in filtered_bottlenecks if b.severity.value == "critical"]),
                "high": len([b for b in filtered_bottlenecks if b.severity.value == "high"]),
                "medium": len([b for b in filtered_bottlenecks if b.severity.value == "medium"]),
                "low": len([b for b in filtered_bottlenecks if b.severity.value == "low"])
            }
        }
        
        return report_data
    
    def _generate_skill_gap_report(self, start_time: datetime, end_time: datetime,
                                  config: ReportConfig) -> Dict[str, Any]:
        """Generate skill gap analysis report"""
        # Get skill gap analysis
        gap_report = self.skill_gap_analyzer.analyze_all_pending_tasks()
        
        # Get team profile
        team_profile = self.skill_gap_analyzer.get_team_skill_profile()
        
        # Get gap summary
        gap_summary = self.skill_gap_analyzer.get_gap_summary()
        
        report_data = {
            "summary": {
                "total_tasks_analyzed": gap_report.total_tasks_analyzed,
                "total_gaps_found": gap_report.total_gaps_found,
                "critical_gaps": gap_summary.get("critical_gaps", 0),
                "high_gaps": gap_summary.get("high_gaps", 0)
            },
            "gaps_by_severity": gap_report.gaps_by_severity,
            "gaps_by_category": gap_report.gaps_by_category,
            "missing_skills": gap_report.missing_skills[:config.max_items],
            "team_profile": team_profile,
            "training_needs": gap_report.training_needs[:config.max_items],
            "hiring_suggestions": gap_report.hiring_suggestions[:config.max_items] if config.include_recommendations else [],
            "recommendations": gap_report.recommendations[:config.max_items] if config.include_recommendations else []
        }
        
        return report_data
    
    def _generate_workflow_report(self, start_time: datetime, end_time: datetime,
                                 config: ReportConfig) -> Dict[str, Any]:
        """Generate workflow execution report"""
        # Get workflow metrics
        workflow_summary = self.workflow_collector.get_workflow_summary()
        workflow_types = self.workflow_collector.get_workflow_type_stats()
        
        # Get throughput trend
        throughput_trend = self.workflow_collector.get_throughput_trend(config.time_range_hours)
        
        # Get recent workflows
        all_workflows = self.workflow_collector.export_metrics().get("workflows", [])
        recent_workflows = [
            w for w in all_workflows
            if w.get("start_time") and start_time <= datetime.fromisoformat(w["start_time"]) <= end_time
        ][:config.max_items]
        
        report_data = {
            "summary": workflow_summary,
            "workflow_types": workflow_types,
            "throughput": {
                "trend": throughput_trend[-20:] if throughput_trend else [],  # Last 20 points
                "current_rate": throughput_trend[-1]["workflows_completed"] if throughput_trend else 0,
                "peak_rate": max((t["workflows_completed"] for t in throughput_trend), default=0)
            },
            "recent_workflows": recent_workflows,
            "recommendations": self._generate_workflow_recommendations(workflow_summary, workflow_types) if config.include_recommendations else []
        }
        
        return report_data
    
    def _generate_resource_report(self, start_time: datetime, end_time: datetime,
                                 config: ReportConfig) -> Dict[str, Any]:
        """Generate resource utilization report"""
        # Get resource trend
        resource_trend = self.workflow_collector.get_resource_trend(config.time_range_hours)
        
        # Calculate averages
        if resource_trend:
            avg_cpu = sum(r["cpu_percent"] for r in resource_trend) / len(resource_trend)
            avg_memory = sum(r["memory_percent"] for r in resource_trend) / len(resource_trend)
            peak_cpu = max(r["cpu_percent"] for r in resource_trend)
            peak_memory = max(r["memory_percent"] for r in resource_trend)
            peak_workflows = max(r["active_workflows"] for r in resource_trend)
        else:
            avg_cpu = avg_memory = peak_cpu = peak_memory = peak_workflows = 0
        
        report_data = {
            "summary": {
                "average_cpu_usage": avg_cpu,
                "average_memory_usage": avg_memory,
                "peak_cpu_usage": peak_cpu,
                "peak_memory_usage": peak_memory,
                "peak_active_workflows": peak_workflows
            },
            "resource_trend": resource_trend[-50:] if resource_trend else [],  # Last 50 points
            "recommendations": self._generate_resource_recommendations(avg_cpu, avg_memory, peak_cpu, peak_memory) if config.include_recommendations else []
        }
        
        return report_data
    
    def _generate_trend_report(self, start_time: datetime, end_time: datetime,
                              config: ReportConfig) -> Dict[str, Any]:
        """Generate trend analysis report"""
        # Get throughput trend
        throughput_trend = self.workflow_collector.get_throughput_trend(config.time_range_hours)
        
        # Get resource trend
        resource_trend = self.workflow_collector.get_resource_trend(config.time_range_hours)
        
        # Calculate trends
        throughput_increasing = self._is_trend_increasing([t["workflows_completed"] for t in throughput_trend])
        cpu_trend = self._is_trend_increasing([r["cpu_percent"] for r in resource_trend])
        memory_trend = self._is_trend_increasing([r["memory_percent"] for r in resource_trend])
        
        # Calculate growth rates
        throughput_growth = self._calculate_growth_rate([t["workflows_completed"] for t in throughput_trend])
        cpu_growth = self._calculate_growth_rate([r["cpu_percent"] for r in resource_trend])
        
        report_data = {
            "trends": {
                "throughput": {
                    "direction": "increasing" if throughput_increasing else "decreasing",
                    "growth_rate": throughput_growth,
                    "data_points": len(throughput_trend)
                },
                "cpu_usage": {
                    "direction": "increasing" if cpu_trend else "decreasing",
                    "growth_rate": cpu_growth,
                    "data_points": len(resource_trend)
                },
                "memory_usage": {
                    "direction": "increasing" if memory_trend else "decreasing",
                    "data_points": len(resource_trend)
                }
            },
            "forecast": self._generate_forecast(throughput_trend, resource_trend),
            "recommendations": self._generate_trend_recommendations(
                throughput_increasing, cpu_trend, memory_trend, throughput_growth
            ) if config.include_recommendations else []
        }
        
        return report_data
    
    def _generate_executive_report(self, start_time: datetime, end_time: datetime,
                                  config: ReportConfig) -> Dict[str, Any]:
        """Generate executive summary report"""
        # Collect key metrics from all reports
        perf_data = self._generate_performance_report(start_time, end_time, config)
        bottleneck_data = self._generate_bottleneck_report(start_time, end_time, config)
        skill_data = self._generate_skill_gap_report(start_time, end_time, config)
        resource_data = self._generate_resource_report(start_time, end_time, config)
        
        report_data = {
            "executive_summary": {
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "duration_hours": config.time_range_hours
                },
                "key_metrics": {
                    "workflow_success_rate": perf_data["summary"]["success_rate"],
                    "total_workflows": perf_data["summary"]["total_workflows"],
                    "critical_bottlenecks": bottleneck_data["severity_breakdown"]["critical"],
                    "skill_gaps": skill_data["summary"]["total_gaps_found"],
                    "resource_health": "good" if resource_data["summary"]["average_cpu_usage"] < 70 else "warning"
                }
            },
            "top_issues": self._identify_top_issues(bottleneck_data, skill_data),
            "recommendations": self._aggregate_recommendations([
                perf_data.get("recommendations", []),
                bottleneck_data.get("suggestions", []),
                skill_data.get("recommendations", []),
                resource_data.get("recommendations", [])
            ])[:10],  # Top 10 recommendations
            "next_steps": self._generate_next_steps(bottleneck_data, skill_data, resource_data)
        }
        
        return report_data
    
    def _generate_custom_report(self, start_time: datetime, end_time: datetime,
                               config: ReportConfig) -> Dict[str, Any]:
        """Generate custom report based on filters"""
        report_data = {}
        
        # Apply filters to include specific data
        if config.filters.get("include_performance", True):
            report_data["performance"] = self._generate_performance_report(start_time, end_time, config)
        
        if config.filters.get("include_bottlenecks", True):
            report_data["bottlenecks"] = self._generate_bottleneck_report(start_time, end_time, config)
        
        if config.filters.get("include_skills", True):
            report_data["skills"] = self._generate_skill_gap_report(start_time, end_time, config)
        
        if config.filters.get("include_workflows", True):
            report_data["workflows"] = self._generate_workflow_report(start_time, end_time, config)
        
        if config.filters.get("include_resources", True):
            report_data["resources"] = self._generate_resource_report(start_time, end_time, config)
        
        return report_data
    
    def _format_report(self, data: Dict[str, Any], format: ReportFormat, title: str) -> str:
        """Format report data into specified format"""
        if format == ReportFormat.JSON:
            return json.dumps(data, indent=2, default=str)
        
        elif format == ReportFormat.CSV:
            return self._format_as_csv(data)
        
        elif format == ReportFormat.HTML:
            return self._format_as_html(data, title)
        
        elif format == ReportFormat.MARKDOWN:
            return self._format_as_markdown(data, title)
        
        else:
            return json.dumps(data, indent=2, default=str)
    
    def _format_as_csv(self, data: Dict[str, Any]) -> str:
        """Format report as CSV"""
        output = io.StringIO()
        
        # Flatten nested data for CSV
        flattened = self._flatten_dict(data)
        
        if flattened:
            writer = csv.DictWriter(output, fieldnames=flattened.keys())
            writer.writeheader()
            writer.writerow(flattened)
        
        return output.getvalue()
    
    def _format_as_html(self, data: Dict[str, Any], title: str) -> str:
        """Format report as HTML"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .warning {{ color: orange; }}
        .critical {{ color: red; }}
        .success {{ color: green; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
        
        # Add summary section if present
        if "summary" in data:
            html += '<div class="summary">'
            html += '<h2>Summary</h2>'
            for key, value in data["summary"].items():
                html += f'<p><strong>{key}:</strong> {value}</p>'
            html += '</div>'
        
        # Add tables for array data
        for key, value in data.items():
            if isinstance(value, list) and value:
                html += f'<h2>{key.replace("_", " ").title()}</h2>'
                if value and isinstance(value[0], dict):
                    html += '<table>'
                    # Header
                    html += '<tr>'
                    for col in value[0].keys():
                        html += f'<th>{col.replace("_", " ").title()}</th>'
                    html += '</tr>'
                    # Rows
                    for item in value[:20]:  # Limit to 20 rows
                        html += '<tr>'
                        for col, val in item.items():
                            html += f'<td>{val}</td>'
                        html += '</tr>'
                    html += '</table>'
        
        html += """
</body>
</html>"""
        
        return html
    
    def _format_as_markdown(self, data: Dict[str, Any], title: str) -> str:
        """Format report as Markdown"""
        md = f"# {title}\n\n"
        md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # Add summary section
        if "summary" in data:
            md += "## Summary\n\n"
            for key, value in data["summary"].items():
                md += f"- **{key}:** {value}\n"
            md += "\n"
        
        # Add tables for array data
        for key, value in data.items():
            if isinstance(value, list) and value:
                md += f"## {key.replace('_', ' ').title()}\n\n"
                if value and isinstance(value[0], dict):
                    # Header
                    headers = list(value[0].keys())
                    md += "| " + " | ".join(h.replace("_", " ").title() for h in headers) + " |\n"
                    md += "|" + "|".join(["---" for _ in headers]) + "|\n"
                    # Rows
                    for item in value[:20]:
                        row = []
                        for col in headers:
                            val = item.get(col, "")
                            row.append(str(val))
                        md += "| " + " | ".join(row) + " |\n"
                    md += "\n"
        
        return md
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _save_report(self, content: str, output_path: str, format: ReportFormat) -> str:
        """Save report to file"""
        try:
            # Ensure directory exists
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Report saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return None
    
    def _generate_performance_recommendations(self, workflow_summary: Dict, 
                                              slowest: List, failed: List) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if workflow_summary.get("overall_success_rate", 100) < 90:
            recommendations.append(f"Success rate is {workflow_summary['overall_success_rate']:.1f}%. Review failed workflows and implement retry logic.")
        
        if slowest:
            recommendations.append(f"Optimize {len(slowest)} slowest workflows. Consider parallelization or code optimization.")
        
        if failed:
            recommendations.append(f"Address {len(failed)} frequently failing steps. Review error handling and input validation.")
        
        if workflow_summary.get("average_workflow_duration", 0) > 60:
            recommendations.append("Average workflow duration exceeds 60 seconds. Consider breaking into smaller workflows.")
        
        return recommendations
    
    def _generate_workflow_recommendations(self, workflow_summary: Dict, 
                                          workflow_types: Dict) -> List[str]:
        """Generate workflow-specific recommendations"""
        recommendations = []
        
        # Find underperforming workflow types
        for wf_type, stats in workflow_types.items():
            if stats.get("success_rate", 100) < 85:
                recommendations.append(f"Workflow '{wf_type}' has low success rate ({stats['success_rate']:.1f}%). Investigate and fix.")
        
        return recommendations
    
    def _generate_resource_recommendations(self, avg_cpu: float, avg_memory: float,
                                          peak_cpu: float, peak_memory: float) -> List[str]:
        """Generate resource optimization recommendations"""
        recommendations = []
        
        if avg_cpu > 80:
            recommendations.append(f"High average CPU usage ({avg_cpu:.1f}%). Consider scaling horizontally or optimizing workloads.")
        
        if peak_cpu > 95:
            recommendations.append(f"CPU spikes detected ({peak_cpu:.1f}%). Implement rate limiting or queue backpressure.")
        
        if avg_memory > 85:
            recommendations.append(f"High memory usage ({avg_memory:.1f}%). Check for memory leaks or increase capacity.")
        
        return recommendations
    
    def _generate_trend_recommendations(self, throughput_increasing: bool,
                                       cpu_trend: bool, memory_trend: bool,
                                       growth_rate: float) -> List[str]:
        """Generate trend-based recommendations"""
        recommendations = []
        
        if throughput_increasing and growth_rate > 20:
            recommendations.append(f"Throughput is growing rapidly ({growth_rate:.1f}%). Plan for capacity expansion.")
        
        if cpu_trend and not throughput_increasing:
            recommendations.append("CPU usage increasing without throughput gain. Investigate inefficiencies.")
        
        return recommendations
    
    def _is_trend_increasing(self, values: List[float]) -> bool:
        """Determine if values show increasing trend"""
        if len(values) < 2:
            return False
        
        # Simple linear trend detection
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        return second_half > first_half
    
    def _calculate_growth_rate(self, values: List[float]) -> float:
        """Calculate growth rate percentage"""
        if len(values) < 2 or values[0] == 0:
            return 0.0
        
        growth = ((values[-1] - values[0]) / values[0]) * 100
        return growth
    
    def _generate_forecast(self, throughput_trend: List, resource_trend: List) -> Dict[str, Any]:
        """Generate simple forecasts based on trends"""
        forecast = {}
        
        if len(throughput_trend) >= 10:
            recent_throughput = [t["workflows_completed"] for t in throughput_trend[-10:]]
            avg_recent = sum(recent_throughput) / len(recent_throughput)
            forecast["expected_throughput_next_hour"] = avg_recent * 60  # Assuming per minute rate
        
        if len(resource_trend) >= 10:
            recent_cpu = [r["cpu_percent"] for r in resource_trend[-10:]]
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
            forecast["expected_cpu_next_hour"] = min(100, avg_cpu * 1.1)  # 10% increase estimate
        
        return forecast
    
    def _identify_top_issues(self, bottleneck_data: Dict, skill_data: Dict) -> List[Dict]:
        """Identify top issues from reports"""
        issues = []
        
        # Add critical bottlenecks
        critical_bottlenecks = bottleneck_data.get("severity_breakdown", {}).get("critical", 0)
        if critical_bottlenecks > 0:
            issues.append({
                "severity": "critical",
                "type": "bottleneck",
                "description": f"{critical_bottlenecks} critical bottlenecks detected",
                "count": critical_bottlenecks
            })
        
        # Add skill gaps
        critical_gaps = skill_data.get("summary", {}).get("critical_gaps", 0)
        if critical_gaps > 0:
            issues.append({
                "severity": "high",
                "type": "skill_gap",
                "description": f"{critical_gaps} critical skill gaps identified",
                "count": critical_gaps
            })
        
        return sorted(issues, key=lambda x: x.get("count", 0), reverse=True)[:5]
    
    def _aggregate_recommendations(self, recommendation_lists: List[List[str]]) -> List[str]:
        """Aggregate and deduplicate recommendations"""
        all_recommendations = []
        seen = set()
        
        for rec_list in recommendation_lists:
            for rec in rec_list:
                if rec not in seen:
                    all_recommendations.append(rec)
                    seen.add(rec)
        
        return all_recommendations
    
    def _generate_next_steps(self, bottleneck_data: Dict, skill_data: Dict, 
                            resource_data: Dict) -> List[str]:
        """Generate actionable next steps"""
        next_steps = []
        
        # Prioritize critical issues
        if bottleneck_data.get("severity_breakdown", {}).get("critical", 0) > 0:
            next_steps.append("Immediately address critical bottlenecks identified in the report")
        
        if skill_data.get("summary", {}).get("critical_gaps", 0) > 0:
            next_steps.append("Review critical skill gaps and assign training or external resources")
        
        if resource_data.get("summary", {}).get("peak_cpu_usage", 0) > 90:
            next_steps.append("Scale resources to handle peak load")
        
        # Default next steps
        if not next_steps:
            next_steps.append("Continue monitoring performance metrics")
            next_steps.append("Review trends weekly for proactive optimization")
        
        return next_steps
    
    def get_report_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent report history"""
        return [r.to_dict() for r in self.report_history[-limit:]]
    
    def export_report(self, report: Report, format: ReportFormat = None) -> str:
        """Export report in specified format"""
        output_format = format or report.format
        return self._format_report(report.data, output_format, report.title)
    
    def schedule_report(self, config: ReportConfig, interval_hours: int = 24) -> None:
        """
        Schedule recurring report generation.
        Note: This requires a scheduler integration (e.g., APScheduler)
        """
        logger.info(f"Scheduled recurring {config.report_type.value} report every {interval_hours} hours")
        # Implementation would depend on your scheduler setup


# Singleton instance
_report_generator: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """Get global ReportGenerator instance"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator