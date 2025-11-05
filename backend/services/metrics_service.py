import requests
from typing import Dict, Any, Optional
from datetime import datetime
from .scaling_service import get_stack_info


def query_prometheus(mimir_url: str, promql_query: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Query Prometheus/Mimir API with PromQL.
    
    Args:
        mimir_url: Base URL of Mimir instance (e.g., http://nlb-dns/mimir)
        promql_query: PromQL query string
        timeout: Request timeout in seconds
    
    Returns:
        Dict with query results or error
    """
    url = f"{mimir_url}/prometheus/api/v1/query"
    
    params = {
        "query": promql_query,
        "time": datetime.now().isoformat()
    }
    
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "errorType": "network_error"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "errorType": "unknown_error"
        }


def get_stack_metrics(stack_id: str) -> Dict[str, Any]:
    """
    Get key metrics for a specific stack.
    
    Queries:
    - Average CPU usage (%)
    - Average Memory usage (%)
    - Instance count
    
    Args:
        stack_id: Stack identifier
    
    Returns:
        Dict with metric values and query status
    """
    try:
        # Get stack info to find Mimir endpoint
        stack_info = get_stack_info(stack_id)
        nlb_dns = stack_info.get("nlb_dns")
        
        if not nlb_dns:
            return {
                "error": "NLB DNS not found for stack",
                "stack_id": stack_id,
                "metrics": {}
            }
        
        mimir_url = f"http://{nlb_dns}/mimir"
        
        # Query CPU usage
        # Note: node_exporter needs to be running on instances with label stack_id
        # For now, we'll query without stack_id filter and average all
        cpu_query = 'avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) * 100'
        cpu_result = query_prometheus(mimir_url, cpu_query)
        
        cpu_usage = 0.0
        if cpu_result.get("status") == "success" and cpu_result.get("data", {}).get("result"):
            try:
                cpu_usage = float(cpu_result["data"]["result"][0]["value"][1])
            except (IndexError, KeyError, ValueError):
                cpu_usage = 0.0
        
        # Query Memory usage
        memory_query = '(1 - avg(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        memory_result = query_prometheus(mimir_url, memory_query)
        
        memory_usage = 0.0
        if memory_result.get("status") == "success" and memory_result.get("data", {}).get("result"):
            try:
                memory_usage = float(memory_result["data"]["result"][0]["value"][1])
            except (IndexError, KeyError, ValueError):
                memory_usage = 0.0
        
        # Query instance count (up metric)
        instance_count_query = 'count(up{job="node"})'
        instance_result = query_prometheus(mimir_url, instance_count_query)
        
        instance_count = stack_info.get("current_instance_count", 0)
        if instance_result.get("status") == "success" and instance_result.get("data", {}).get("result"):
            try:
                instance_count = int(float(instance_result["data"]["result"][0]["value"][1]))
            except (IndexError, KeyError, ValueError):
                pass
        
        return {
            "stack_id": stack_id,
            "metrics": {
                "avg_cpu_percent": round(cpu_usage, 2),
                "avg_memory_percent": round(memory_usage, 2),
                "instance_count": instance_count
            },
            "mimir_url": mimir_url,
            "query_time": datetime.now().isoformat()
        }
    
    except ValueError as e:
        return {
            "error": str(e),
            "stack_id": stack_id,
            "metrics": {}
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "stack_id": stack_id,
            "metrics": {}
        }


def query_custom_metric(stack_id: str, promql_query: str) -> Dict[str, Any]:
    """
    Run a custom PromQL query against stack's Mimir instance.
    
    Args:
        stack_id: Stack identifier
        promql_query: Custom PromQL query
    
    Returns:
        Raw Prometheus API response
    """
    try:
        stack_info = get_stack_info(stack_id)
        nlb_dns = stack_info.get("nlb_dns")
        
        if not nlb_dns:
            return {
                "status": "error",
                "error": "NLB DNS not found for stack"
            }
        
        mimir_url = f"http://{nlb_dns}/mimir"
        return query_prometheus(mimir_url, promql_query)
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


