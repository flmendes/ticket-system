// ticket-system-k6-stress.js
// Stress test with gradual ramp-up to avoid "too many open files"
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

/* ------------------------------------
   1️⃣  Configuração de cenários com RAMP-UP
------------------------------------ */
export let options = {
  stages: [
    // Ramp-up gradual para evitar "too many open files"
    { duration: '30s', target: 50 },   // 0 → 50 VUs em 30s
    { duration: '30s', target: 100 },  // 50 → 100 VUs em 30s
    { duration: '30s', target: 150 },  // 100 → 150 VUs em 30s
    { duration: '30s', target: 200 },  // 150 → 200 VUs em 30s
    { duration: '2m', target: 200 },   // Manter 200 VUs por 2min
    { duration: '30s', target: 100 },  // Ramp-down 200 → 100
    { duration: '30s', target: 0 },    // Ramp-down 100 → 0
  ],

  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],     // Menos de 1% de falhas
    purchase_success: ["rate>0"],
  },
};

/* ------------------------------------
   2️⃣  Métrica customizada
------------------------------------ */
export let purchase_success = new Rate("purchase_success");

/* ------------------------------------
   3️⃣  Valores de ambiente com fallback
------------------------------------ */
const BASE_URL = __ENV.VU_BASE_URL ?? "http://localhost:8002";
const VACANCY_URL = __ENV.VU_VACANCY_URL ?? "http://localhost:8001";
const QTY = parseInt(__ENV.QTY ?? "1", 10);

/* ------------------------------------
   4️⃣  Funções de teste
------------------------------------ */

/** Consulta a quantidade de vagas disponíveis. */
export function availability() {
  const res = http.get(`${VACANCY_URL}/api/v1/available`, {
    timeout: '10s', // Timeout maior para alta carga
  });

  check(res, {
    "status is 200": (r) => r.status === 200,
    "has qty field": (r) => r.json("qty") !== undefined,
  });

  sleep(0.5);
}

/** Tenta comprar QTY ingressos. */
export function purchase() {
  const payload = JSON.stringify({ qty: QTY });
  const params = {
    headers: { "Content-Type": "application/json" },
    timeout: '10s', // Timeout maior para alta carga
  };

  const res = http.post(`${BASE_URL}/api/v1/purchase`, payload, params);

  const ok = check(res, {
    "status is 200": (r) => r.status === 200,
    "success true": (r) => r.json("success") === true,
  });

  if (ok) purchase_success.add(1);

  sleep(0.5);
}

/* ------------------------------------
   5️⃣  Cenário principal
------------------------------------ */
export default function () {
  // Alternar entre availability e purchase
  if (__VU % 2 === 0) {
    availability();
  } else {
    purchase();
  }
}
