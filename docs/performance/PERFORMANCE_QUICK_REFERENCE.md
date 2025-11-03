# Performance Quick Reference

## 🎯 Baseline v1.0.0 - Métricas-Chave

**Data**: 2025-11-02 | **Status**: ✅ BASELINE ESTABELECIDO

---

## Métricas Críticas

| Métrica | Baseline v1.0.0 | Threshold Alerta | Status |
|---------|-----------------|------------------|--------|
| **P95 Latency** | 10.75ms | > 50ms | ✅ |
| **Avg Latency** | 4.61ms | > 25ms | ✅ |
| **Throughput** | 197.86 req/s | < 180 req/s | ✅ |
| **HTTP Failures** | 0% | > 0% | ✅ |
| **Purchase Success** | 100% | < 100% | ✅ |

---

## Teste de Carga Padrão

```bash
# Configuração
VUs: 100 (50 availability + 50 purchase)
Duration: 60s
Total Requests: 11,950

# Comando
k6 run ticket-system-k6.js --out json=performance-results.json
```

---

## Interpretação Rápida

### ✅ Sistema Saudável Se:
- P95 < 50ms
- Throughput > 180 req/s
- HTTP Failures = 0%
- Purchase Success = 100% (até esgotar estoque)

### ⚠️ Investigar Se:
- P95 entre 50-100ms
- Throughput entre 150-180 req/s
- HTTP Failures < 1%

### 🚨 Problema Crítico Se:
- P95 > 100ms
- Throughput < 150 req/s
- HTTP Failures > 1%
- Purchase Success < 100% (com estoque disponível)

---

## Comparação v1.0.0 vs Arquitetura Antiga

| Métrica | Antes | v1.0.0 | Melhoria |
|---------|-------|--------|----------|
| P95 Latency | ~257ms | 10.75ms | 🚀 **96%** |
| Avg Latency | ~101ms | 4.61ms | 🚀 **95%** |
| Throughput | ~166 req/s | 197.86 req/s | ✅ **19%** |

---

## Melhorias Implementadas

- ✅ HTTP Client Pooling (30-50% mais rápido)
- ✅ Response Caching (reduz contenção)
- ✅ Timeouts Otimizados (5s → 2s)
- ✅ Arquitetura em Camadas
- ✅ API Versioning (/api/v1)
- ✅ Middleware GZip
- ✅ Health Checks

---

## Capacidade do Sistema

```
Throughput Sustentável: ~200 req/s
Concorrência Máxima: 100-150 VUs
Latência P95: < 11ms
Estoque: 1000 tickets/min (testado)
```

---

## Quick Check

```bash
# Verificar serviços rodando
curl http://localhost:8001/api/v1/health
curl http://localhost:8002/api/v1/health

# Teste rápido de disponibilidade
curl http://localhost:8001/api/v1/available

# Teste rápido de compra
curl -X POST http://localhost:8002/api/v1/purchase \
  -H "Content-Type: application/json" \
  -d '{"qty": 1}'

# Teste de carga completo
k6 run ticket-system-k6.js
```

---

## Arquivos de Referência

- 📊 **Análise Completa**: `PERFORMANCE_BASELINE.md`
- 📁 **Resultado Texto**: `performance-baseline-v1.0.0.txt`
- 📁 **Dados JSON**: `performance-baseline-v1.0.0.json`
- 📝 **Script K6**: `ticket-system-k6.js`

---

## Quando Re-executar Testes

Execute após:
- ✅ Mudanças na lógica de negócio
- ✅ Alterações em configurações de performance
- ✅ Atualizações de dependências importantes
- ✅ Mudanças na arquitetura ou infraestrutura
- ✅ Releases de produção (validação)

**NÃO é necessário** para:
- ❌ Mudanças de UI/frontend apenas
- ❌ Alterações de documentação
- ❌ Refatorações sem mudança de lógica

---

**Última Atualização**: 2025-11-02
**Próxima Revisão Recomendada**: Após qualquer mudança significativa
