// ticket-system-k6.js
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

/* ------------------------------------
   1️⃣  Configuração de cenários
------------------------------------ */
export let options = {
  scenarios: {
    availability: {
      executor: "constant-vus",
      vus: 50,
      duration: "1m",
      exec: "availability",
    },

    purchase: {
      executor: "constant-vus",
      vus: 50,
      duration: "1m",
      exec: "purchase",
    },
  },

  thresholds: {
    http_req_duration: ["p(95)<500"],
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
  const res = http.get(`${VACANCY_URL}/api/v1/available`);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "has qty field": (r) => r.json("qty") !== undefined,
  });

  sleep(0.5);
}

/** Tenta comprar QTY ingressos. */
export function purchase() {
  const payload = JSON.stringify({ qty: QTY });
  const params = { headers: { "Content-Type": "application/json" } };

  const res = http.post(`${BASE_URL}/api/v1/purchase`, payload, params);

  const ok = check(res, {
    "status is 200": (r) => r.status === 200,
    "success true": (r) => r.json("success") === true,
  });

  if (ok) purchase_success.add(1);

  sleep(0.5);
}
