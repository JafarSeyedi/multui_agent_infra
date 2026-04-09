import logging
from typing import Optional, Union
from redis.asyncio import Redis, Sentinel
from redis.asyncio.cluster import RedisCluster
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

class RedisManager:
    """
    Advanced Redis Connection Manager supporting Cluster, Sentinel, and Standalone.
    Implements production-grade retry policies and pooling.
    """
    def __init__(self, config: dict):
        self.config = config
        self.client: Optional[Union[Redis, RedisCluster]] = None
        self._retry = Retry(ExponentialBackoff(cap=10, base=1), 3)
        self.logger = logging.getLogger("RedisManager")

    async def connect(self):
        mode = self.config.get("mode", "standalone")
        
        try:
            if mode == "cluster":
                self.client = RedisCluster(
                    host=self.config["host"], 
                    port=self.config["port"],
                    decode_responses=True,
                    retry=self._retry,
                    auto_close_connection_pool=True
                )
            elif mode == "sentinel":
                sentinel = Sentinel(self.config["nodes"], decode_responses=True)
                self.client = sentinel.master_for(self.config["master_name"])
            else:
                self.client = Redis(
                    host=self.config.get("host", "localhost"),
                    port=self.config.get("port", 6379),
                    db=self.config.get("db", 0),
                    decode_responses=True,
                    retry=self._retry,
                    health_check_interval=30
                )
            
            await self.client.ping()
            self.logger.info(f"🚀 Connected to Redis in {mode} mode.")
        except Exception as e:
            self.logger.error(f"❌ Redis connection failed: {e}")
            raise

    async def get_client(self) -> Optional[Union[Redis, RedisCluster]]:
        if not self.client:
            await self.connect()
        return self.client
