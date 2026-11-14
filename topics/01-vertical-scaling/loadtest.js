import http from 'k6/http';
import { check, sleep } from 'k6';

// SD-01 Vertical Scaling lab — k6 load test.
// Run the API first (see README.md), then run this from this folder:
//
//   k6 run loadtest.js
//
// What it does: 50 virtual users hit /cpu for 30 seconds, with a
// 10-second ramp-up. k6 reports requests/sec, p95 latency, and errors.
// Run it once against 1 worker, once against 4 workers, and compare.

export const options = {
  stages: [
    { duration: '10s', target: 50 }, // ramp up to 50 virtual users
    { duration: '30s', target: 50 }, // hold 50 virtual users
    { duration: '5s', target: 0 },   // ramp down
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],      // <1% errors
    http_req_duration: ['p(95)<2000'],   // p95 under 2s (will fail on 1 worker — that is the point)
  },
};

export default function () {
  const res = http.get('http://127.0.0.1:8000/cpu');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'has result': (r) => JSON.parse(r.body).result !== undefined,
  });
  sleep(0.1);
}
