// ticket-system-k6-k8s.js
// Load test for Kubernetes deployment via Ingress
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Counter } from "k6/metrics";
import { htmlReport } from "https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.1/index.js";

/* ------------------------------------
   📊 Custom Metrics
------------------------------------ */
const purchaseSuccess = new Rate("purchase_success");
const purchaseFailure = new Rate("purchase_failure");
const healthCheckSuccess = new Rate("health_check_success");
const totalPurchases = new Counter("total_purchases");

/* ------------------------------------
   ⚙️  Test Configuration
------------------------------------ */
export const options = {
  scenarios: {
    // Scenario 1: Health checks - low load, constant
    health_checks: {
      executor: "constant-vus",
      vus: 10,
      duration: "2m",
      exec: "healthCheck",
    },

    // Scenario 2: Purchase load - ramped load
    purchase_load: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 20 },   // Warm-up
        { duration: "1m", target: 50 },    // Ramp to 50
        { duration: "1m", target: 100 },   // Ramp to 100
        { duration: "2m", target: 100 },   // Sustain 100
        { duration: "30s", target: 50 },   // Ramp down
        { duration: "30s", target: 0 },    // Cool down
      ],
      exec: "purchaseTickets",
    },
  },

  thresholds: {
    // HTTP metrics
    "http_req_duration": ["p(95)<200", "p(99)<500"],  // 95% < 200ms, 99% < 500ms
    "http_req_failed": ["rate<0.01"],                  // < 1% failures

    // Custom metrics
    "purchase_success": ["rate>0.95"],                 // > 95% success rate
    "health_check_success": ["rate>0.99"],             // > 99% health checks ok

    // Scenario-specific thresholds
    "http_req_duration{scenario:purchase_load}": ["p(95)<250"],
    "http_req_duration{scenario:health_checks}": ["p(95)<100"],
  },
};

/* ------------------------------------
   🌐 Configuration
------------------------------------ */
const BASE_URL = __ENV.K8S_URL || "http://ticket.127.0.0.1.nip.io";
const QTY = parseInt(__ENV.QTY || "1", 10);

console.log(`
╔══════════════════════════════════════════════╗
║  K6 Load Test - Kubernetes Deployment       ║
╠══════════════════════════════════════════════╣
║  Base URL: ${BASE_URL.padEnd(30)} ║
║  Quantity per purchase: ${String(QTY).padEnd(18)} ║
║  Duration: ~6 minutes                        ║
╚══════════════════════════════════════════════╝
`);

/* ------------------------------------
   🏥 Health Check Scenario
------------------------------------ */
export function healthCheck() {
  const res = http.get(`${BASE_URL}/api/v1/health`, {
    tags: { name: "HealthCheck" },
    timeout: "5s",
  });

  const success = check(res, {
    "health: status is 200": (r) => r.status === 200,
    "health: response has status field": (r) => {
      try {
        return r.json("status") !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  healthCheckSuccess.add(success);
  sleep(1); // Health checks every 1 second
}

/* ------------------------------------
   🎫 Purchase Tickets Scenario
------------------------------------ */
export function purchaseTickets() {
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
    "purchase: status is 200 or 400": (r) => r.status === 200 || r.status === 400,
    "purchase: has success field": (r) => {
      try {
        return r.json("success") !== undefined;
      } catch (e) {
        return false;
      }
    },
    "purchase: has message": (r) => {
      try {
        return r.json("message") !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  totalPurchases.add(1);

  // Check if purchase was successful
  try {
    const data = res.json();
    if (data.success === true) {
      purchaseSuccess.add(1);
    } else {
      purchaseFailure.add(1);
    }
  } catch (e) {
    purchaseFailure.add(1);
  }

  sleep(0.3); // Small delay between purchases
}

/* ------------------------------------
   📋 Summary Report
------------------------------------ */
export function handleSummary(data) {
  console.log(`
╔══════════════════════════════════════════════╗
║           Test Summary                       ║
╚══════════════════════════════════════════════╝
  `);

  return {
    "k8s-test-summary.html": htmlReport(data),
    stdout: textSummary(data, { indent: " ", enableColors: true }),
    "k8s-test-results.json": JSON.stringify(data, null, 2),
  };
}

/* ------------------------------------
   🚀 Setup & Teardown
------------------------------------ */
export function setup() {
  console.log("⚙️  Setting up test...");

  // Verify service is accessible
  const res = http.get(`${BASE_URL}/`);
  if (res.status !== 200) {
    console.error(`❌ Service not accessible at ${BASE_URL}`);
    console.error(`   Status: ${res.status}`);
    throw new Error("Service not accessible");
  }

  console.log("✅ Service is accessible");
  console.log(`   Response: ${res.body.substring(0, 100)}...`);

  return { startTime: new Date().toISOString() };
}

export function teardown(data) {
  console.log(`
╔══════════════════════════════════════════════╗
║  Test Completed                              ║
╠══════════════════════════════════════════════╣
║  Start: ${data.startTime.padEnd(32)} ║
║  End:   ${new Date().toISOString().padEnd(32)} ║
╚══════════════════════════════════════════════╝
  `);
}
