import os
import re
import json
import requests
from typing import Dict, Any
from .scaling_service import get_stack_info
from .metrics_service import get_stack_metrics
from ..core.config import settings


def analyze_and_recommend(stack_id: str) -> Dict[str, Any]:
    """
    Analyze stack metrics using AI and provide scaling recommendation.
    
    Args:
        stack_id: Stack identifier
    
    Returns:
        Dict with stack info, metrics, and AI recommendation
    """
    try:
        # Get current stack information
        stack_info = get_stack_info(stack_id)
        current_count = stack_info["current_instance_count"]
        
        # Get current metrics
        metrics_data = get_stack_metrics(stack_id)
        
        if "error" in metrics_data:
            # If we can't get metrics, return no_change
            return {
                "stack_id": stack_id,
                "current_count": current_count,
                "metrics": {},
                "recommendation": {
                    "action": "no_change",
                    "target_count": current_count,
                    "reason": f"Unable to fetch metrics: {metrics_data.get('error')}",
                    "confidence": 0.0
                },
                "error": metrics_data.get("error")
            }
        
        metrics = metrics_data.get("metrics", {})
        
        # Call Gemini AI for recommendation
        recommendation = call_gemini_for_recommendation(
            stack_id=stack_id,
            current_count=current_count,
            metrics=metrics
        )
        
        return {
            "stack_id": stack_id,
            "current_count": current_count,
            "metrics": metrics,
            "recommendation": recommendation
        }
    
    except Exception as e:
        return {
            "stack_id": stack_id,
            "error": str(e),
            "recommendation": {
                "action": "no_change",
                "target_count": 1,
                "reason": f"Error analyzing stack: {str(e)}",
                "confidence": 0.0
            }
        }


def call_gemini_for_recommendation(
    stack_id: str,
    current_count: int,
    metrics: Dict[str, float]
) -> Dict[str, Any]:
    """
    Call Gemini API to analyze metrics and recommend scaling action.
    
    Args:
        stack_id: Stack identifier
        current_count: Current number of instances
        metrics: Dict with avg_cpu_percent, avg_memory_percent, etc.
    
    Returns:
        Dict with action, target_count, reason, confidence
    """
    api_key = settings.GEMINI_API_KEY
    
    if not api_key:
        return {
            "action": "no_change",
            "target_count": current_count,
            "reason": "Gemini API key not configured",
            "confidence": 0.0
        }
    
    # Build prompt for Gemini
    cpu = metrics.get("avg_cpu_percent", 0.0)
    memory = metrics.get("avg_memory_percent", 0.0)
    
    prompt = f"""You are an infrastructure scaling advisor. Analyze the following metrics and recommend a scaling action.

Current infrastructure state:
- Stack ID: {stack_id}
- Current EC2 instance count: {current_count}
- Max allowed instances: {settings.SCALE_UP_MAX_INSTANCES}
- Min allowed instances: {settings.SCALE_DOWN_MIN_INSTANCES}

Metrics (5-minute average):
- Average CPU usage: {cpu:.2f}%
- Average Memory usage: {memory:.2f}%

Scaling rules:
1. If CPU > 70% OR Memory > 80%, recommend SCALE_UP by adding 1-2 instances
2. If CPU < 30% AND Memory < 50% AND current_count > min_instances, recommend SCALE_DOWN by removing 1 instance
3. Otherwise, recommend NO_CHANGE

Important constraints:
- target_count must be between {settings.SCALE_DOWN_MIN_INSTANCES} and {settings.SCALE_UP_MAX_INSTANCES}
- Be conservative: only scale if metrics clearly indicate need
- Confidence should be high (>0.7) for actual scaling, lower (<0.6) for no_change

Provide your recommendation in JSON format only (no markdown, no explanation text):
{{
  "action": "scale_up" | "scale_down" | "no_change",
  "target_count": <integer>,
  "reason": "<brief explanation>",
  "confidence": <float between 0.0 and 1.0>
}}"""
    
    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 256,
            "topP": 0.8,
            "topK": 10
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract text from Gemini response
        if "candidates" not in result or not result["candidates"]:
            return fallback_recommendation(current_count, cpu, memory)
        
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Parse JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            recommendation = json.loads(json_match.group(0))
            
            # Validate and sanitize recommendation
            recommendation = validate_recommendation(recommendation, current_count)
            return recommendation
        else:
            return fallback_recommendation(current_count, cpu, memory)
    
    except requests.exceptions.RequestException as e:
        return {
            "action": "no_change",
            "target_count": current_count,
            "reason": f"Gemini API error: {str(e)}",
            "confidence": 0.0
        }
    except json.JSONDecodeError as e:
        return {
            "action": "no_change",
            "target_count": current_count,
            "reason": f"Failed to parse AI response: {str(e)}",
            "confidence": 0.0
        }
    except Exception as e:
        return {
            "action": "no_change",
            "target_count": current_count,
            "reason": f"Unexpected error: {str(e)}",
            "confidence": 0.0
        }


def validate_recommendation(rec: Dict[str, Any], current_count: int) -> Dict[str, Any]:
    """
    Validate and sanitize AI recommendation.
    
    Ensures:
    - action is valid
    - target_count is within bounds
    - confidence is between 0 and 1
    """
    action = rec.get("action", "no_change")
    if action not in ["scale_up", "scale_down", "no_change"]:
        action = "no_change"
    
    target_count = rec.get("target_count", current_count)
    try:
        target_count = int(target_count)
    except (ValueError, TypeError):
        target_count = current_count
    
    # Enforce bounds
    target_count = max(settings.SCALE_DOWN_MIN_INSTANCES, target_count)
    target_count = min(settings.SCALE_UP_MAX_INSTANCES, target_count)
    
    confidence = rec.get("confidence", 0.5)
    try:
        confidence = float(confidence)
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.5
    
    reason = rec.get("reason", "AI recommendation")
    if not isinstance(reason, str):
        reason = "AI recommendation"
    
    return {
        "action": action,
        "target_count": target_count,
        "reason": reason,
        "confidence": confidence
    }


def fallback_recommendation(current_count: int, cpu: float, memory: float) -> Dict[str, Any]:
    """
    Fallback rule-based recommendation when AI is unavailable.
    
    Simple heuristic:
    - CPU > 70% or Memory > 80%: scale up
    - CPU < 30% and Memory < 50% and count > 1: scale down
    - Otherwise: no change
    """
    if cpu > 70.0 or memory > 80.0:
        target = min(current_count + 1, settings.SCALE_UP_MAX_INSTANCES)
        return {
            "action": "scale_up",
            "target_count": target,
            "reason": f"High resource usage (CPU: {cpu:.1f}%, Mem: {memory:.1f}%) - using fallback rules",
            "confidence": 0.8
        }
    elif cpu < 30.0 and memory < 50.0 and current_count > settings.SCALE_DOWN_MIN_INSTANCES:
        target = max(current_count - 1, settings.SCALE_DOWN_MIN_INSTANCES)
        return {
            "action": "scale_down",
            "target_count": target,
            "reason": f"Low resource usage (CPU: {cpu:.1f}%, Mem: {memory:.1f}%) - using fallback rules",
            "confidence": 0.7
        }
    else:
        return {
            "action": "no_change",
            "target_count": current_count,
            "reason": f"Resource usage within normal range (CPU: {cpu:.1f}%, Mem: {memory:.1f}%) - using fallback rules",
            "confidence": 0.6
        }


