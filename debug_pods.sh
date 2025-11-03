#!/bin/bash

echo "=== Debugging Pod Behavior ==="
echo "Current Redis value:"
kubectl exec redis-9ff5f6b65-c2zg2 -n ticket-system -- redis-cli get ticket_stock

echo -e "\n=== Testing 10 purchase requests ==="
for i in {1..10}; do
  echo -n "Request $i: "
  result=$(curl -s http://ticket.127.0.0.1.nip.io/api/v1/purchase -X POST -H "Content-Type: application/json" -d '{"qty": 1}')
  success=$(echo $result | grep -o '"success":[^,]*' | cut -d: -f2)
  remaining=$(echo $result | grep -o '"remaining":[^,]*' | cut -d: -f2)
  echo "success=$success, remaining=$remaining"
  sleep 0.5
done

echo -e "\n=== Final Redis value ==="
kubectl exec redis-9ff5f6b65-c2zg2 -n ticket-system -- redis-cli get ticket_stock

echo -e "\n=== Pod initialization values ==="
echo "Pod c59qj initialized with: 9896"
echo "Pod nxng5 initialized with: 9939"
echo "Current Redis: $(kubectl exec redis-9ff5f6b65-c2zg2 -n ticket-system -- redis-cli get ticket_stock)"