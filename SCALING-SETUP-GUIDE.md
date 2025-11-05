# AI Auto-Scaling Setup and Testing Guide

## Prerequisites

1. Backend running with new code
2. At least one stack deployed via `/elb/deploy`
3. Gemini API key from Google AI Studio
4. Monitoring stack (Grafana/Mimir/Loki) operational

## Step 1: Install New Dependencies

```bash
cd /home/deployer/Documents/VPBANK/code
pip install -r backend/requirements.txt
```

## Step 2: Configure Environment Variables

Add to your `.env` file:

```bash
# AI Advisor
GEMINI_API_KEY=your_gemini_api_key_here

# Auto-scaling configuration
AUTO_SCALING_ENABLED=false  # Set to true to enable automatic scaling
AUTO_SCALING_INTERVAL_MINUTES=5
AUTO_SCALING_CONFIDENCE_THRESHOLD=0.7
SCALE_UP_MAX_INSTANCES=20
SCALE_DOWN_MIN_INSTANCES=1
```

To get Gemini API key:
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy and paste into `.env`

## Step 3: Restart Backend

```bash
# Kill existing backend
pkill -f "uvicorn backend.app"

# Start with new code
cd /home/deployer/Documents/VPBANK/code
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8008 --reload
```

## Step 4: Test Manual Scaling

### 4.1 List Active Stacks

```bash
curl http://localhost:8008/scaling/stacks | jq
```

Expected output:
```json
{
  "success": true,
  "count": 1,
  "stacks": [
    {
      "stack_id": "20251104123456-abc12345",
      "current_instance_count": 1,
      "instances": ["3.xxx.xxx.xxx"],
      "nlb_dns": "test-monitoring-nlb-xxx.elb.ap-southeast-2.amazonaws.com",
      ...
    }
  ]
}
```

### 4.2 Get Stack Info

```bash
STACK_ID="<your_stack_id>"
curl http://localhost:8008/scaling/stack/$STACK_ID/info | jq
```

### 4.3 Manual Scale Up

```bash
curl -X POST http://localhost:8008/scaling/stack/scale \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "'$STACK_ID'",
    "target_count": 2,
    "reason": "Testing manual scale-up"
  }' | jq
```

Expected output:
```json
{
  "success": true,
  "stack_id": "...",
  "old_count": 1,
  "new_count": 2,
  "action": "scale_up",
  "message": "Successfully scaled from 1 to 2 instances",
  "logs": {...}
}
```

**Verification:**
- Check AWS Console → EC2 → Instances (should see 2 instances)
- Check `deploy_metadata.json` in stack workspace (instance_count should be 2)
- Check NLB target group (should have 2 targets)

### 4.4 Manual Scale Down

```bash
curl -X POST http://localhost:8008/scaling/stack/scale \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "'$STACK_ID'",
    "target_count": 1,
    "reason": "Testing manual scale-down (LIFO)"
  }' | jq
```

**Verification:**
- Terraform terminates the highest-index instance (LIFO)
- AWS Console shows only 1 instance remaining

## Step 5: Test Metrics Query

### 5.1 Get Stack Metrics

```bash
curl http://localhost:8008/scaling/stack/$STACK_ID/metrics | jq
```

Expected output:
```json
{
  "success": true,
  "stack_id": "...",
  "metrics": {
    "avg_cpu_percent": 5.23,
    "avg_memory_percent": 42.15,
    "instance_count": 1
  },
  "mimir_url": "http://...",
  "query_time": "2025-11-04T12:34:56"
}
```

**Note:** If metrics are all 0.0, it means:
- Grafana Agent not installed on EC2 instances, OR
- Instances don't have node_exporter running, OR
- Mimir hasn't received data yet

### 5.2 Custom Metrics Query

```bash
curl -X POST http://localhost:8008/scaling/stack/metrics/query \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "'$STACK_ID'",
    "promql_query": "up{job=\"node\"}"
  }' | jq
```

## Step 6: Test AI Recommendation

### 6.1 Get AI Recommendation (No Execute)

```bash
curl -X POST http://localhost:8008/scaling/stack/$STACK_ID/recommend | jq
```

Expected output:
```json
{
  "success": true,
  "stack_id": "...",
  "current_count": 1,
  "metrics": {
    "avg_cpu_percent": 5.23,
    "avg_memory_percent": 42.15,
    "instance_count": 1
  },
  "recommendation": {
    "action": "no_change",
    "target_count": 1,
    "reason": "Resource usage within normal range (CPU: 5.2%, Mem: 42.2%)",
    "confidence": 0.85
  }
}
```

**What Gemini AI Analyzes:**
- Current CPU and memory usage
- Current instance count vs min/max bounds
- Applies rules: CPU > 70% or Mem > 80% → scale_up
- Returns action + confidence score

### 6.2 Test with Simulated Load

To test scale_up recommendation:

1. SSH into EC2:
```bash
ssh -i /path/to/key.pem ubuntu@<instance_ip>
```

2. Generate CPU load:
```bash
sudo apt-get update
sudo apt-get install -y stress
stress --cpu 2 --timeout 300s  # 5 minutes of CPU load
```

3. Wait 2-3 minutes for metrics to update in Mimir

4. Get recommendation again:
```bash
curl -X POST http://localhost:8008/scaling/stack/$STACK_ID/recommend | jq
```

Expected output with high load:
```json
{
  "recommendation": {
    "action": "scale_up",
    "target_count": 2,
    "reason": "High CPU usage detected (85.3%), recommend adding instances",
    "confidence": 0.92
  }
}
```

### 6.3 Auto-Scale with Confidence Threshold

```bash
curl -X POST "http://localhost:8008/scaling/stack/$STACK_ID/auto-scale?confidence_threshold=0.7" | jq
```

**Behavior:**
- If `confidence >= 0.7` AND `action != no_change`: **Executes scaling**
- Otherwise: Returns recommendation only

Expected output when executed:
```json
{
  "success": true,
  "executed": true,
  "recommendation": {...},
  "scaling_result": {
    "success": true,
    "old_count": 1,
    "new_count": 2,
    ...
  }
}
```

## Step 7: Enable Auto-Scaling Scheduler

### 7.1 Update .env

```bash
AUTO_SCALING_ENABLED=true
```

### 7.2 Restart Backend

The scheduler will:
- Start automatically on backend startup
- Run every 5 minutes (configurable)
- Check all active stacks
- Execute scaling if confidence > 0.7

### 7.3 Monitor Scheduler Logs

```bash
# Backend logs will show:
# [2025-11-04 12:00:00] Starting auto-scaling check for all stacks
# [2025-11-04 12:00:01] Found 2 active stack(s)
# [2025-11-04 12:00:02] Stack xxx: Action=no_change, Current=1, Confidence=0.65
# [2025-11-04 12:00:03] Stack xxx: No scaling needed
# [2025-11-04 12:00:04] Auto-scaling check completed
```

### 7.4 Test Auto-Scaling End-to-End

1. Deploy a stack with 1 instance
2. Enable auto-scaling in `.env`
3. SSH into instance and run `stress --cpu 2 --timeout 600s`
4. Wait 5-10 minutes
5. Check logs - should see AI detecting high CPU
6. After confidence threshold met, should auto-scale up to 2 instances
7. Stop stress test
8. Wait 10-15 minutes
9. Should auto-scale down to 1 instance

## Troubleshooting

### Issue: "Gemini API key not configured"

**Solution:** Add `GEMINI_API_KEY` to `.env` and restart backend

### Issue: Metrics all showing 0.0

**Solution:** 
- Instances need Grafana Agent installed
- Use `auto_install_monitoring: true` when deploying
- Or manually install agent on existing instances

### Issue: "Stack metadata not found"

**Solution:**
- Only stacks deployed with new code have metadata
- Redeploy old stacks, or manually create `deploy_metadata.json`

### Issue: Terraform apply fails during scaling

**Solution:**
- Check AWS credentials in `.env`
- Check Terraform state is not locked
- Check instance limits in AWS account

### Issue: Scheduler not running

**Solution:**
- Check `AUTO_SCALING_ENABLED=true` in `.env`
- Check backend startup logs for scheduler initialization
- Verify no errors in scheduler.py imports

## API Documentation

Full API docs available at: http://localhost:8008/docs

Key endpoints:
- `GET /scaling/stacks` - List all stacks
- `GET /scaling/stack/{id}/info` - Stack details
- `GET /scaling/stack/{id}/metrics` - Current metrics
- `POST /scaling/stack/scale` - Manual scaling
- `POST /scaling/stack/{id}/recommend` - AI recommendation only
- `POST /scaling/stack/{id}/auto-scale` - AI recommendation + execute

## Monitoring Scaling Activity

### View Scaling History

```bash
# Check metadata file for last scaling event
STACK_ID="your_stack_id"
cat .infra/work/$STACK_ID/deploy_metadata.json | jq '{
  last_scaled_at,
  last_scale_reason,
  current_count: .context.instance_count
}'
```

### Track Auto-Scaling Decisions

Backend logs include:
- Timestamp of each check
- Stack analyzed
- Metrics values
- AI recommendation
- Action taken (if any)

Recommended: Pipe backend logs to a file for analysis:

```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8008 2>&1 | tee backend-scaling.log
```

## Next Steps

1. Install dependencies and configure `.env`
2. Test manual scaling first
3. Verify metrics collection works
4. Test AI recommendations
5. Enable scheduler for production use
6. Monitor for 24-48 hours to tune confidence threshold

## Configuration Tuning

Based on your workload, you may want to adjust:

- `AUTO_SCALING_INTERVAL_MINUTES`: How often to check (default: 5)
- `AUTO_SCALING_CONFIDENCE_THRESHOLD`: How confident AI must be (default: 0.7)
- `SCALE_UP_MAX_INSTANCES`: Maximum instances allowed (default: 20)
- `SCALE_DOWN_MIN_INSTANCES`: Minimum instances to keep (default: 1)

Lower confidence threshold → more aggressive scaling
Higher confidence threshold → more conservative scaling


