// ticket-system-k6-autoscaling.js
// Load test specifically designed to trigger HPA autoscaling
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Counter } from "k6/metrics";

/* ------------------------------------
   📊 Custom Metrics
------------------------------------ */
const purchaseSuccess = new Rate("purchase_success");
const totalPurchases = new Counter("total_purchases");

/* ------------------------------------
   ⚙️  Autoscaling Test Configuration

   This test gradually increases load to trigger HPA scaling
------------------------------------ */
export const options = {
  stages: [
    // Phase 1: Baseline (2 replicas)
    { duration: "1m", target: 10 },    // Warm-up with low load

    // Phase 2: Gradual increase (should trigger scale to ~4 replicas)
    { duration: "2m", target: 50 },    // Increase load

    // Phase 3: High load (should trigger scale to ~6-8 replicas)
    { duration: "3m", target: 100 },   // High sustained load

    // Phase 4: Peak load (should trigger max scale ~10 replicas)
    { duration: "2m", target: 150 },   // Peak load

    // Phase 5: Sustain peak (verify stability at max)
    { duration: "3m", target: 150 },   // Sustain to observe scaling

    // Phase 6: Gradual decrease (observe scale down behavior)
    { duration: "2m", target: 100 },   // Reduce load
    { duration: "2m", target: 50 },    // Further reduce
    { duration: "1m", target: 10 },    // Cool down
    { duration: "1m", target: 0 },     // Complete stop
  ],

  thresholds: {
    "http_req_duration": ["p(95)<500"],     // Allow higher latency during scaling
    "http_req_failed": ["rate<0.05"],       // Allow 5% failures during scaling events
    "purchase_success": ["rate>0.90"],      // 90% success rate
  },
};

/* ------------------------------------
   🌐 Configuration
------------------------------------ */
const BASE_URL = __ENV.K8S_URL || "http://ticket.127.0.0.1.nip.io";
const QTY = parseInt(__ENV.QTY || "1", 10);

console.log(`
╔══════════════════════════════════════════════╗
║  K6 Autoscaling Test                         ║
╠══════════════════════════════════════════════╣
║  Base URL: ${BASE_URL.padEnd(30)} ║
║  Duration: ~17 minutes                       ║
║  Max VUs: 150                                ║
║  Expected scaling: 2 → 10 → 2 replicas       ║
╚══════════════════════════════════════════════╝

Watch scaling with:
  kubectl get hpa -n ticket-system -w
  kubectl get pods -n ticket-system -w
`);

/* ------------------------------------
   🎫 Main Test Function
------------------------------------ */
export default function () {
  const payload = JSON.stringify({ qty: QTY });
  const params = {
    headers: {
      "Content-Type": "application/json",
    },
    tags: { name: "PurchaseTickets" },
    timeout: "10s",
  };

  const res = http.post(`${BASE_URL}/api/v1/purchase`, payload, params);

  const success = check(res, {
    "status is 200 or 400": (r) => r.status === 200 || r.status === 400,
    "has success field": (r) => {
      try {
        return r.json("success") !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  totalPurchases.add(1);

  // Track business success
  try {
    const data = res.json();
    if (data.success === true) {
      purchaseSuccess.add(1);
    } else {
      purchaseSuccess.add(0);
    }
  } catch (e) {
    purchaseSuccess.add(0);
  }

  // Small delay to create CPU load
  sleep(0.1);
}

/* ------------------------------------
   🚀 Setup & Teardown
------------------------------------ */
export function setup() {
  console.log("\n⚙️  Starting autoscaling test...");
  console.log("📊 Monitor HPA in another terminal:");
  console.log("   kubectl get hpa -n ticket-system -w\n");

  // Verify service is accessible
  const res = http.get(`${BASE_URL}/`);
  if (res.status !== 200) {
    console.error(`❌ Service not accessible at ${BASE_URL}`);
    throw new Error("Service not accessible");
  }

  console.log("✅ Service is accessible");
  console.log("🚀 Starting load test...\n");

  return { startTime: new Date().toISOString() };
}

export function teardown(data) {
  console.log(`
╔══════════════════════════════════════════════╗
║  Autoscaling Test Completed                  ║
╠══════════════════════════════════════════════╣
║  Start: ${data.startTime.padEnd(32)} ║
║  End:   ${new Date().toISOString().padEnd(32)} ║
╚══════════════════════════════════════════════╝

Check final pod count:
  kubectl get pods -n ticket-system

Check HPA events:
  kubectl describe hpa -n ticket-system
  `);
}
