import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .scaling_service import list_active_stacks, scale_stack
from .ai_advisor import analyze_and_recommend
from ..core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create scheduler instance
scheduler = BackgroundScheduler()


def auto_scale_all_stacks():
    """
    Check all active stacks and scale if AI recommends with high confidence.
    
    This function:
    1. Lists all active stacks
    2. For each stack, gets AI recommendation
    3. If confidence > threshold and action != no_change, executes scaling
    4. Logs all actions
    """
    if not settings.AUTO_SCALING_ENABLED:
        logger.debug("Auto-scaling is disabled, skipping check")
        return
    
    logger.info("Starting auto-scaling check for all stacks")
    
    try:
        stacks = list_active_stacks()
        logger.info(f"Found {len(stacks)} active stack(s)")
        
        for stack in stacks:
            stack_id = stack["stack_id"]
            
            try:
                logger.info(f"Analyzing stack: {stack_id}")
                
                # Get AI recommendation
                result = analyze_and_recommend(stack_id)
                
                if "error" in result:
                    logger.warning(f"Stack {stack_id}: Error getting recommendation - {result['error']}")
                    continue
                
                recommendation = result["recommendation"]
                action = recommendation["action"]
                confidence = recommendation["confidence"]
                target_count = recommendation["target_count"]
                current_count = result["current_count"]
                
                logger.info(
                    f"Stack {stack_id}: "
                    f"Action={action}, "
                    f"Current={current_count}, "
                    f"Target={target_count}, "
                    f"Confidence={confidence:.2f}, "
                    f"Reason={recommendation['reason']}"
                )
                
                # Check if we should execute
                should_execute = (
                    action != "no_change" and
                    confidence >= settings.AUTO_SCALING_CONFIDENCE_THRESHOLD
                )
                
                if should_execute:
                    logger.info(
                        f"Stack {stack_id}: Executing {action} "
                        f"(confidence {confidence:.2f} >= threshold {settings.AUTO_SCALING_CONFIDENCE_THRESHOLD:.2f})"
                    )
                    
                    scale_result = scale_stack(
                        stack_id=stack_id,
                        target_count=target_count,
                        reason=f"AI Auto-scale: {recommendation['reason']}"
                    )
                    
                    if scale_result.get("success"):
                        logger.info(
                            f"Stack {stack_id}: Successfully scaled from "
                            f"{scale_result['old_count']} to {scale_result['new_count']} instances"
                        )
                    else:
                        logger.error(
                            f"Stack {stack_id}: Scaling failed - {scale_result.get('error', 'Unknown error')}"
                        )
                else:
                    if action == "no_change":
                        logger.info(f"Stack {stack_id}: No scaling needed")
                    else:
                        logger.info(
                            f"Stack {stack_id}: Skipping {action} "
                            f"(confidence {confidence:.2f} < threshold {settings.AUTO_SCALING_CONFIDENCE_THRESHOLD:.2f})"
                        )
            
            except Exception as e:
                logger.error(f"Stack {stack_id}: Unexpected error - {str(e)}", exc_info=True)
                continue
        
        logger.info("Auto-scaling check completed")
    
    except Exception as e:
        logger.error(f"Auto-scaling check failed: {str(e)}", exc_info=True)


def start_scheduler():
    """
    Start the auto-scaling scheduler.
    
    Schedules auto_scale_all_stacks() to run at configured interval.
    """
    if not settings.AUTO_SCALING_ENABLED:
        logger.info("Auto-scaling is disabled, scheduler will not start")
        return
    
    interval_minutes = settings.AUTO_SCALING_INTERVAL_MINUTES
    
    logger.info(
        f"Starting auto-scaling scheduler "
        f"(interval: {interval_minutes} minutes, "
        f"confidence threshold: {settings.AUTO_SCALING_CONFIDENCE_THRESHOLD})"
    )
    
    # Add job with interval trigger
    scheduler.add_job(
        auto_scale_all_stacks,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="auto_scale_all_stacks",
        name="Auto-scale all stacks based on AI recommendations",
        replace_existing=True
    )
    
    # Start scheduler
    scheduler.start()
    logger.info("Auto-scaling scheduler started successfully")


def stop_scheduler():
    """
    Stop the auto-scaling scheduler gracefully.
    """
    if scheduler.running:
        logger.info("Stopping auto-scaling scheduler")
        scheduler.shutdown(wait=True)
        logger.info("Auto-scaling scheduler stopped")


