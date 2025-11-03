# ADR 002: Kubernetes HPA for Automatic Scaling

**Status**: Accepted

**Date**: 2025-11-02

**Deciders**: Development Team, Operations Team

---

## Context

The ticket system experiences variable load:
- **Normal**: 10-50 req/s
- **Peak**: 500-1000+ req/s (events, sales launches)
- **Overnight**: < 5 req/s

Manual scaling requires:
- Operations team availability 24/7
- Prediction of traffic patterns
- Risk of under-provisioning (outages) or over-provisioning (waste)

---

## Decision

Implement **Kubernetes HorizontalPodAutoscaler (HPA)** with:

**Configuration**:
- Min Replicas: 2 (high availability)
- Max Replicas: 10 (cost control)
- CPU Target: 70%
- Memory Target: 80%

**Scaling Policies**:
```yaml
Scale Up: Aggressive
  - 0s stabilization (immediate)
  - 100% increase OR +4 pods per 30s
  - Chooses maximum

Scale Down: Conservative
  - 300s stabilization (5 minutes)
  - 50% decrease OR -2 pods per 60s
  - Chooses minimum
```

---

## Consequences

### Positive

✅ **Cost Efficiency**: Scales down to 2 pods during low traffic (80% cost reduction)
✅ **Performance**: Scales up to 10 pods in 30s (handles traffic spikes)
✅ **Reliability**: Never goes below 2 replicas (high availability)
✅ **Zero Ops**: No manual intervention required
✅ **Proven Results**: Tested with 1056 req/s, 100% success rate

### Negative

⚠️ **Metrics Server Required**: Additional infrastructure component
⚠️ **Resource Requests Mandatory**: Must define CPU/memory requests
⚠️ **Scale-Down Delay**: 5 minutes before scaling down (by design)
⚠️ **Complexity**: More moving parts to monitor

### Risks Mitigated

🛡️ **Capacity Limit**: Max 10 replicas prevents runaway scaling
🛡️ **Flapping**: 5-minute stabilization prevents constant scaling
🛡️ **Cold Starts**: Min 2 replicas ensures immediate capacity

---

## Alternatives Considered

### 1. Fixed Replicas
- ❌ Wastes resources during low traffic
- ❌ Insufficient during peaks
- ✅ Simple

### 2. Manual Scaling
- ❌ Requires 24/7 operations
- ❌ Slow response to traffic changes
- ❌ Human error prone

### 3. Schedule-Based Scaling
- ❌ Doesn't handle unexpected traffic
- ❌ Requires pattern prediction
- ✅ Predictable costs

### 4. Custom Metrics (RPS, Latency)
- ⏸️ Deferred: Requires Prometheus setup
- ✅ More accurate
- ❌ More complex

---

## Implementation Details

**Prerequisites**:
- Metrics Server installed in cluster
- Resource requests defined in deployments
- HPA manifests deployed

**Files**:
- `k8s/vacancy-hpa.yaml`
- `k8s/ticket-hpa.yaml`

**Test Results** (60s load test):
```
Before: 2 + 2 = 4 pods
During: 10 + 8 = 18 pods (scaled in 30s)
After:  2 + 2 = 4 pods (scaled down in 10min)

Performance:
- 63,464 requests
- 1,056 req/s
- 0% errors
```

---

## Validation

**Success Criteria**:
- ✅ Scales up when CPU > 70% or Memory > 80%
- ✅ Scales down when both below target for 5min
- ✅ Never goes below minReplicas (2)
- ✅ Never exceeds maxReplicas (10)
- ✅ Zero errors during scaling events

**Monitoring**:
```bash
kubectl get hpa -n ticket-system
kubectl top pods -n ticket-system
```

---

## Future Enhancements

1. **Custom Metrics**: Scale based on RPS or P95 latency
2. **Predictive Scaling**: ML-based traffic prediction
3. **Cluster Autoscaler**: Automatically add nodes when needed
4. **Multi-Metric**: Combine CPU + Memory + RPS

---

## References

- [AUTOSCALING_GUIDE.md](../guides/AUTOSCALING_GUIDE.md)
- [Kubernetes HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [HPA Best Practices](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/#best-practices)

---

**Related ADRs**: None
