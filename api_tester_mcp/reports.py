"""HTML report generation for test results"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from .models import TestResult, TestSession
from jinja2 import Template


class ReportGenerator:
    """Generate HTML reports for test results"""
    
    def __init__(self):
        self.html_template = self._get_html_template()
    
    def generate_api_test_report(self, results: List[TestResult], session: TestSession) -> str:
        """Generate HTML report for API test results"""
        # Calculate summary statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == "passed")
        failed_tests = sum(1 for r in results if r.status == "failed")
        total_time = sum(r.execution_time for r in results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        # Group results by status
        passed_results = [r for r in results if r.status == "passed"]
        failed_results = [r for r in results if r.status == "failed"]
        
        # Generate report data
        report_data = {
            "title": "API Test Report",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_time": total_time,
                "average_time": avg_time
            },
            "results": {
                "passed": self._format_api_results(passed_results),
                "failed": self._format_api_results(failed_results)
            },
            "session_info": {
                "id": session.id,
                "spec_type": session.spec_type.value,
                "created_at": session.created_at,
                "scenarios_count": len(session.scenarios),
                "test_cases_count": len(session.test_cases)
            }
        }
        
        return self.html_template.render(**report_data)
    
    def generate_load_test_report(self, results: Dict[str, Any], session: TestSession) -> str:
        """Generate HTML report for load test results"""
        summary = results.get("summary", {})
        response_times = results.get("response_times", {})
        status_codes = results.get("status_codes", {})
        
        report_data = {
            "title": "Load Test Report",
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "response_times": response_times,
            "status_codes": status_codes,
            "session_info": {
                "id": session.id,
                "spec_type": session.spec_type.value,
                "created_at": session.created_at
            },
            "is_load_test": True
        }
        
        return self.html_template.render(**report_data)
    
    def _format_api_results(self, results: List[TestResult]) -> List[Dict[str, Any]]:
        """Format API test results for HTML display"""
        formatted_results = []
        
        for result in results:
            formatted_result = {
                "test_case_id": result.test_case_id,
                "status": result.status,
                "execution_time": f"{result.execution_time:.3f}s",
                "response_status": result.response_status,
                "assertions_passed": result.assertions_passed,
                "assertions_failed": result.assertions_failed,
                "assertion_details": result.assertion_details,
                "error_message": result.error_message,
                "response_preview": self._get_response_preview(result.response_body)
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _get_response_preview(self, response_body: Optional[str], max_length: int = 200) -> str:
        """Get a preview of the response body"""
        if not response_body:
            return ""
        
        try:
            # Try to parse as JSON and format nicely
            parsed = json.loads(response_body)
            formatted = json.dumps(parsed, indent=2)
            if len(formatted) <= max_length:
                return formatted
            return formatted[:max_length] + "..."
        except:
            # Return as-is if not JSON
            if len(response_body) <= max_length:
                return response_body
            return response_body[:max_length] + "..."
    
    def _get_html_template(self) -> Template:
        """Get the HTML template for reports"""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header .timestamp {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .summary-card h3 {
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .summary-card .value {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }
        
        .success-rate {
            color: #27ae60;
        }
        
        .failed-count {
            color: #e74c3c;
        }
        
        .section {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            overflow: hidden;
        }
        
        .section-header {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .section-header h2 {
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-content {
            padding: 20px;
        }
        
        .test-result {
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }
        
        .test-result-header {
            background: #f8f9fa;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .test-result-header.passed {
            border-left: 4px solid #27ae60;
        }
        
        .test-result-header.failed {
            border-left: 4px solid #e74c3c;
        }
        
        .test-id {
            font-family: monospace;
            font-size: 0.9rem;
            color: #666;
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-badge.passed {
            background: #d4edda;
            color: #155724;
        }
        
        .status-badge.failed {
            background: #f8d7da;
            color: #721c24;
        }
        
        .test-details {
            padding: 15px;
            background: #fdfdfd;
        }
        
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .detail-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .detail-label {
            font-weight: 600;
            color: #666;
        }
        
        .detail-value {
            font-family: monospace;
            color: #333;
        }
        
        .assertions {
            margin-top: 15px;
        }
        
        .assertion {
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 5px;
            font-size: 0.9rem;
        }
        
        .assertion.passed {
            background: #d4edda;
            color: #155724;
        }
        
        .assertion.failed {
            background: #f8d7da;
            color: #721c24;
        }
        
        .response-preview {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .load-test-chart {
            margin: 20px 0;
        }
        
        .metric-bar {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }
        
        .metric-label {
            width: 80px;
            font-size: 0.9rem;
            color: #666;
        }
        
        .metric-value {
            margin-left: 10px;
            font-family: monospace;
            font-weight: bold;
        }
        
        .no-results {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 40px;
        }
        
        .session-info {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .session-info h3 {
            color: #1976d2;
            margin-bottom: 10px;
        }
        
        .session-detail {
            display: inline-block;
            margin-right: 20px;
            color: #424242;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .test-result-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="timestamp">Generated on {{ timestamp }}</div>
        </div>
        
        <div class="session-info">
            <h3>Session Information</h3>
            <span class="session-detail"><strong>Session ID:</strong> {{ session_info.id }}</span>
            <span class="session-detail"><strong>Spec Type:</strong> {{ session_info.spec_type }}</span>
            <span class="session-detail"><strong>Created:</strong> {{ session_info.created_at }}</span>
            {% if session_info.scenarios_count %}
            <span class="session-detail"><strong>Scenarios:</strong> {{ session_info.scenarios_count }}</span>
            {% endif %}
            {% if session_info.test_cases_count %}
            <span class="session-detail"><strong>Test Cases:</strong> {{ session_info.test_cases_count }}</span>
            {% endif %}
        </div>
        
        {% if is_load_test %}
        <!-- Load Test Report -->
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Requests</h3>
                <div class="value">{{ summary.total_requests }}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value success-rate">{{ "%.1f"|format(summary.success_rate) }}%</div>
            </div>
            <div class="summary-card">
                <h3>Avg Response Time</h3>
                <div class="value">{{ "%.0f"|format(response_times.average * 1000) }}ms</div>
            </div>
            <div class="summary-card">
                <h3>Requests/sec</h3>
                <div class="value">{{ "%.1f"|format(summary.requests_per_second) }}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2>📊 Response Time Statistics</h2>
            </div>
            <div class="section-content">
                <div class="metric-bar">
                    <span class="metric-label">Average:</span>
                    <span class="metric-value">{{ "%.0f"|format(response_times.average * 1000) }}ms</span>
                </div>
                <div class="metric-bar">
                    <span class="metric-label">P50:</span>
                    <span class="metric-value">{{ "%.0f"|format(response_times.p50 * 1000) }}ms</span>
                </div>
                <div class="metric-bar">
                    <span class="metric-label">P90:</span>
                    <span class="metric-value">{{ "%.0f"|format(response_times.p90 * 1000) }}ms</span>
                </div>
                <div class="metric-bar">
                    <span class="metric-label">P95:</span>
                    <span class="metric-value">{{ "%.0f"|format(response_times.p95 * 1000) }}ms</span>
                </div>
                <div class="metric-bar">
                    <span class="metric-label">P99:</span>
                    <span class="metric-value">{{ "%.0f"|format(response_times.p99 * 1000) }}ms</span>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2>📈 Status Code Distribution</h2>
            </div>
            <div class="section-content">
                {% for status_code, count in status_codes.items() %}
                <div class="metric-bar">
                    <span class="metric-label">{{ status_code }}:</span>
                    <span class="metric-value">{{ count }} requests</span>
                </div>
                {% endfor %}
            </div>
        </div>
        
        {% else %}
        <!-- API Test Report -->
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{{ summary.total_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="value success-rate">{{ summary.passed_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="value failed-count">{{ summary.failed_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="value success-rate">{{ "%.1f"|format(summary.success_rate) }}%</div>
            </div>
            <div class="summary-card">
                <h3>Total Time</h3>
                <div class="value">{{ "%.2f"|format(summary.total_time) }}s</div>
            </div>
            <div class="summary-card">
                <h3>Avg Time</h3>
                <div class="value">{{ "%.3f"|format(summary.average_time) }}s</div>
            </div>
        </div>
        
        {% if results.passed %}
        <div class="section">
            <div class="section-header">
                <h2>✅ Passed Tests ({{ results.passed|length }})</h2>
            </div>
            <div class="section-content">
                {% for result in results.passed %}
                <div class="test-result">
                    <div class="test-result-header passed">
                        <div class="test-id">{{ result.test_case_id }}</div>
                        <div class="status-badge passed">{{ result.status }}</div>
                    </div>
                    <div class="test-details">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="detail-label">Execution Time:</span>
                                <span class="detail-value">{{ result.execution_time }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Response Status:</span>
                                <span class="detail-value">{{ result.response_status }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Assertions Passed:</span>
                                <span class="detail-value">{{ result.assertions_passed }}</span>
                            </div>
                        </div>
                        
                        {% if result.assertion_details %}
                        <div class="assertions">
                            {% for assertion in result.assertion_details %}
                            <div class="assertion {{ 'passed' if assertion.passed else 'failed' }}">
                                {{ assertion.message }}
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                        
                        {% if result.response_preview %}
                        <div class="response-preview">{{ result.response_preview }}</div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if results.failed %}
        <div class="section">
            <div class="section-header">
                <h2>❌ Failed Tests ({{ results.failed|length }})</h2>
            </div>
            <div class="section-content">
                {% for result in results.failed %}
                <div class="test-result">
                    <div class="test-result-header failed">
                        <div class="test-id">{{ result.test_case_id }}</div>
                        <div class="status-badge failed">{{ result.status }}</div>
                    </div>
                    <div class="test-details">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="detail-label">Execution Time:</span>
                                <span class="detail-value">{{ result.execution_time }}</span>
                            </div>
                            {% if result.response_status %}
                            <div class="detail-item">
                                <span class="detail-label">Response Status:</span>
                                <span class="detail-value">{{ result.response_status }}</span>
                            </div>
                            {% endif %}
                            <div class="detail-item">
                                <span class="detail-label">Assertions Failed:</span>
                                <span class="detail-value">{{ result.assertions_failed }}</span>
                            </div>
                        </div>
                        
                        {% if result.error_message %}
                        <div class="assertion failed">
                            <strong>Error:</strong> {{ result.error_message }}
                        </div>
                        {% endif %}
                        
                        {% if result.assertion_details %}
                        <div class="assertions">
                            {% for assertion in result.assertion_details %}
                            <div class="assertion {{ 'passed' if assertion.passed else 'failed' }}">
                                {{ assertion.message }}
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                        
                        {% if result.response_preview %}
                        <div class="response-preview">{{ result.response_preview }}</div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if not results.passed and not results.failed %}
        <div class="section">
            <div class="section-content">
                <div class="no-results">No test results to display</div>
            </div>
        </div>
        {% endif %}
        {% endif %}
    </div>
</body>
</html>
        """
        return Template(template_str)
