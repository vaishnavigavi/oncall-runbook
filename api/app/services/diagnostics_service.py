import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DiagnosticsService:
    """Service for providing read-only diagnostics tools"""
    
    def __init__(self):
        self.logs_dir = "/app/data/mock/logs"
        self.queue_data_dir = "/app/data/mock/queues"
        
    def get_recent_logs(self, service: str) -> Dict[str, Any]:
        """Get recent logs for a service (last 2-3 lines)"""
        try:
            log_file = os.path.join(self.logs_dir, f"{service}.log")
            
            if not os.path.exists(log_file):
                return {
                    "success": False,
                    "error": f"Log file not found: {service}.log",
                    "suggestion": f"Check if {service} service is running and logging to {log_file}"
                }
            
            # Read last 3 lines from the log file
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-3:] if len(lines) >= 3 else lines
            
            # Clean up the lines
            cleaned_lines = [line.strip() for line in recent_lines if line.strip()]
            
            if not cleaned_lines:
                return {
                    "success": False,
                    "error": f"No recent log entries found in {service}.log",
                    "suggestion": f"Log file exists but is empty or contains only whitespace"
                }
            
            return {
                "success": True,
                "service": service,
                "log_file": f"{service}.log",
                "recent_lines": cleaned_lines,
                "line_count": len(cleaned_lines)
            }
            
        except Exception as e:
            logger.error(f"Error reading logs for {service}: {e}")
            return {
                "success": False,
                "error": f"Failed to read logs: {str(e)}",
                "suggestion": "Check file permissions and disk space"
            }
    
    def get_queue_depth(self, queue: str) -> Dict[str, Any]:
        """Get queue depth for a specific queue"""
        try:
            # Check if queue data file exists
            queue_file = os.path.join(self.queue_data_dir, f"{queue}.txt")
            
            if not os.path.exists(queue_file):
                return {
                    "success": False,
                    "error": f"Queue depth tool not configured for {queue}",
                    "suggestion": "Verify queue depth manually or configure monitoring",
                    "tool_status": "not_configured"
                }
            
            # Read queue depth from file
            with open(queue_file, 'r') as f:
                content = f.read().strip()
                
            try:
                depth = int(content)
                return {
                    "success": True,
                    "queue": queue,
                    "depth": depth,
                    "status": "active" if depth > 0 else "empty",
                    "tool_status": "configured"
                }
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid queue depth format in {queue}.txt",
                    "suggestion": "Check queue depth manually",
                    "tool_status": "malformed"
                }
                
        except Exception as e:
            logger.error(f"Error reading queue depth for {queue}: {e}")
            return {
                "success": False,
                "error": f"Failed to read queue depth: {str(e)}",
                "suggestion": "Check queue depth manually",
                "tool_status": "error"
            }
    
    def suggest_diagnostics_tools(self, query: str) -> Dict[str, Any]:
        """Light router to suggest relevant diagnostics tools based on query content"""
        query_lower = query.lower()
        
        suggestions = {
            "logs": [],
            "queues": [],
            "tools_available": False,
            "reasoning": []
        }
        
        # CPU & deployment related queries → suggest logs
        if any(term in query_lower for term in ['cpu', 'deploy', 'deployment', 'spike', 'performance', 'slow']):
            suggestions["logs"].extend(['app', 'nginx', 'system'])
            suggestions["reasoning"].append("CPU/deployment issues often show in application and system logs")
            suggestions["tools_available"] = True
        
        # Queue related queries → suggest queue depth
        if any(term in query_lower for term in ['queue', 'dlq', 'backlog', 'processing', 'jobs', 'tasks']):
            suggestions["queues"].extend(['main', 'dlq', 'processing', 'email'])
            suggestions["reasoning"].append("Queue issues require checking depth and processing status")
            suggestions["tools_available"] = True
        
        # Redis/cache related queries → no tools needed
        if any(term in query_lower for term in ['redis', 'cache', 'hit rate', 'miss rate', 'memory']):
            suggestions["reasoning"].append("Redis/cache issues typically require specialized monitoring tools")
            suggestions["tools_available"] = False
        
        # Database related queries → suggest logs
        if any(term in query_lower for term in ['database', 'db', 'query', 'connection', 'timeout']):
            suggestions["logs"].extend(['app', 'database', 'system'])
            suggestions["reasoning"].append("Database issues often appear in application and database logs")
            suggestions["tools_available"] = True
        
        # Network related queries → suggest logs
        if any(term in query_lower for term in ['network', 'timeout', 'connection', 'http', 'api']):
            suggestions["logs"].extend(['nginx', 'app', 'system'])
            suggestions["reasoning"].append("Network issues appear in web server and application logs")
            suggestions["tools_available"] = True
        
        return suggestions
    
    def run_diagnostics(self, query: str) -> Dict[str, Any]:
        """Run diagnostics based on query content and return results"""
        suggestions = self.suggest_diagnostics_tools(query)
        
        results = {
            "query": query,
            "suggestions": suggestions,
            "logs": {},
            "queues": {},
            "tools_ran": False,
            "summary": []
        }
        
        # Run log diagnostics if suggested
        for service in suggestions["logs"]:
            log_result = self.get_recent_logs(service)
            results["logs"][service] = log_result
            if log_result["success"]:
                results["tools_ran"] = True
                results["summary"].append(f"✅ {service} logs: {log_result['line_count']} recent entries")
            else:
                results["summary"].append(f"❌ {service} logs: {log_result['error']}")
        
        # Run queue diagnostics if suggested
        for queue in suggestions["queues"]:
            queue_result = self.get_queue_depth(queue)
            results["queues"][queue] = queue_result
            if queue_result["success"]:
                results["tools_ran"] = True
                results["summary"].append(f"✅ {queue} queue: {queue_result['depth']} items")
            else:
                results["summary"].append(f"❌ {queue} queue: {queue_result['error']}")
        
        return results

