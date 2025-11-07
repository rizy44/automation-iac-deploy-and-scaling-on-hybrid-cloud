from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
from ..services.scaling_service import get_stack_info, list_active_stacks, scale_stack
from ..services.metrics_service import get_stack_metrics, query_custom_metric
from ..services.ai_advisor import analyze_and_recommend
from ..core.config import settings

router = APIRouter(prefix="/scaling", tags=["scaling"])


class ScaleRequest(BaseModel):
    stack_id: str
    target_count: int = Field(ge=1, le=20, description="Target number of EC2 instances")
    reason: Optional[str] = Field(None, description="Reason for scaling")


class MetricsQueryRequest(BaseModel):
    stack_id: str
    promql_query: str = Field(..., description="PromQL query to execute")


@router.get("/stacks")
def list_stacks():
    """
    List all active stacks with current instance counts.
    
    Returns:
        List of stack information dicts
    """
    try:
        stacks = list_active_stacks()
        return {
            "success": True,
            "count": len(stacks),
            "stacks": stacks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stack/{stack_id}/info")
def get_stack(stack_id: str):
    """
    Get detailed information about a specific stack.
    
    Args:
        stack_id: Stack identifier
    
    Returns:
        Stack information including instance count, IPs, NLB DNS, deployment time
    """
    try:
        info = get_stack_info(stack_id)
        return {
            "success": True,
            "stack": info
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stack/{stack_id}/metrics")
def get_metrics(stack_id: str):
    """
    Get current metrics for a stack from Mimir.
    
    Args:
        stack_id: Stack identifier
    
    Returns:
        Current CPU, memory usage and instance count
    """
    try:
        metrics = get_stack_metrics(stack_id)
        
        if "error" in metrics:
            return {
                "success": False,
                "error": metrics["error"],
                "stack_id": stack_id
            }
        
        return {
            "success": True,
            **metrics
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stack/metrics/query")
def query_metrics(req: MetricsQueryRequest):
    """
    Execute a custom PromQL query against stack's Mimir instance.
    
    Args:
        req: Request with stack_id and promql_query
    
    Returns:
        Raw Prometheus API response
    """
    try:
        result = query_custom_metric(req.stack_id, req.promql_query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stack/scale")
def scale(req: ScaleRequest):
    """
    Manually scale a stack to target instance count.
    
    This will:
    1. Validate target count is within bounds
    2. Re-render Terraform with new instance_count
    3. Run terraform apply
    4. Update metadata
    
    Uses LIFO (Last In First Out) for scale-down.
    
    Args:
        req: Scale request with stack_id, target_count, reason
    
    Returns:
        Scaling result with old/new counts and logs
    """
    try:
        result = scale_stack(
            stack_id=req.stack_id,
            target_count=req.target_count,
            reason=req.reason or "Manual scaling via API"
        )
        
        if not result.get("success"):
            # Propagate terraform logs to client for easier debugging
            raise HTTPException(
                status_code=500,
                detail={
                    "error": result.get("error", "Scaling failed"),
                    "stack_id": req.stack_id,
                    "logs": result.get("logs", {}),
                    "old_count": result.get("old_count"),
                    "target_count": result.get("target_count")
                }
            )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stack/{stack_id}/recommend")
def get_recommendation(stack_id: str):
    """
    Get AI-powered scaling recommendation without executing.
    
    This will:
    1. Fetch current metrics from Mimir
    2. Send metrics to Gemini AI
    3. Return recommendation with confidence score
    
    No scaling action is taken - this is read-only.
    
    Args:
        stack_id: Stack identifier
    
    Returns:
        Current metrics and AI recommendation
    """
    try:
        result = analyze_and_recommend(stack_id)
        
        if "error" in result and result.get("recommendation", {}).get("confidence", 0) == 0:
            return {
                "success": False,
                "error": result["error"],
                **result
            }
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stack/{stack_id}/auto-scale")
def auto_scale(stack_id: str, confidence_threshold: Optional[float] = None):
    """
    Get AI recommendation and auto-execute if confidence is above threshold.
    
    This combines:
    1. Get AI recommendation
    2. If confidence > threshold AND action != no_change: execute scaling
    3. Return recommendation and scaling result (if executed)
    
    Args:
        stack_id: Stack identifier
        confidence_threshold: Minimum confidence to execute (default from settings)
    
    Returns:
        Recommendation and scaling result if executed
    """
    if confidence_threshold is None:
        confidence_threshold = settings.AUTO_SCALING_CONFIDENCE_THRESHOLD
    
    try:
        # Get AI recommendation
        result = analyze_and_recommend(stack_id)
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "recommendation": result.get("recommendation"),
                "executed": False
            }
        
        recommendation = result["recommendation"]
        action = recommendation["action"]
        confidence = recommendation["confidence"]
        target_count = recommendation["target_count"]
        
        # Check if we should execute
        should_execute = (
            action != "no_change" and
            confidence >= confidence_threshold
        )
        
        if should_execute:
            # Execute scaling
            scale_result = scale_stack(
                stack_id=stack_id,
                target_count=target_count,
                reason=f"AI Auto-scale: {recommendation['reason']}"
            )
            
            return {
                "success": True,
                "executed": True,
                "recommendation": recommendation,
                "scaling_result": scale_result,
                **result
            }
        else:
            return {
                "success": True,
                "executed": False,
                "reason": f"Confidence {confidence:.2f} below threshold {confidence_threshold:.2f}" if confidence < confidence_threshold else "No scaling needed",
                "recommendation": recommendation,
                **result
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


