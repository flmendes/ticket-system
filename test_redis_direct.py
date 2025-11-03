#!/usr/bin/env python3
"""
Script para testar diretamente a conexão e operações com Redis.
"""
import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, '/Users/flavio/Developer/Labs/python/ticket-system/src')

from common.redis_client import RedisStockManager


async def test_redis_directly():
    """Testa Redis diretamente sem a aplicação."""
    print("🔧 Testando conexão direta com Redis...")
    
    try:
        # Conectar ao Redis
        redis_manager = RedisStockManager(redis_url="redis://localhost:6379/0")
        print("   ✅ RedisStockManager criado")
        
        # Conectar
        await redis_manager.connect()
        print("   ✅ Conexão estabelecida")
        
        # Inicializar stock
        await redis_manager.initialize_stock(10000)
        print("   ✅ Stock inicializado com 10000")
        
        # Verificar stock atual
        current = await redis_manager.get_current()
        print(f"   ✅ Stock atual: {current}")
        
        # Testar reserva
        success, remaining = await redis_manager.reserve(5)
        print(f"   ✅ Reserva de 5: success={success}, remaining={remaining}")
        
        # Verificar stock após reserva
        current_after = await redis_manager.get_current()
        print(f"   ✅ Stock após reserva: {current_after}")
        
        # Health check
        health = await redis_manager.health_check()
        print(f"   ✅ Health check: {health}")
        
        # Fechar conexão
        await redis_manager.close()
        print("   ✅ Conexão fechada")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_redis_keys():
    """Verifica as chaves no Redis."""
    print("\n🔍 Verificando chaves no Redis...")
    
    try:
        import redis.asyncio as aioredis
        
        redis = aioredis.from_url("redis://localhost:6379/0", decode_responses=True)
        
        # Listar todas as chaves
        keys = await redis.keys("*")
        print(f"   Chaves encontradas: {keys}")
        
        # Se houver chave de stock, mostrar valor
        if "ticket_stock" in keys:
            stock_value = await redis.get("ticket_stock")
            print(f"   ✅ ticket_stock = {stock_value}")
        else:
            print("   ⚠️  Chave 'ticket_stock' não encontrada")
        
        # Verificar locks
        lock_keys = [k for k in keys if "lock" in k]
        if lock_keys:
            print(f"   ⚠️  Locks encontrados: {lock_keys}")
            for lock_key in lock_keys:
                lock_value = await redis.get(lock_key)
                ttl = await redis.ttl(lock_key)
                print(f"     {lock_key} = {lock_value} (TTL: {ttl}s)")
        
        await redis.close()
        
    except Exception as e:
        print(f"   ❌ Erro ao verificar chaves: {e}")


async def main():
    """Executa todos os testes."""
    print("🚀 Iniciando testes do Redis\n")
    
    # Teste 1: Verificar chaves existentes
    await test_redis_keys()
    
    # Teste 2: Teste direto do Redis
    redis_ok = await test_redis_directly()
    
    # Teste 3: Verificar chaves após teste
    await test_redis_keys()
    
    if redis_ok:
        print("\n✅ Redis está funcionando corretamente!")
    else:
        print("\n❌ Problemas encontrados no Redis!")


if __name__ == "__main__":
    asyncio.run(main())