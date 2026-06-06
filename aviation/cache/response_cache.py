from functools import lru_cache
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class AssessmentCache:
    """Cache assessment results to avoid duplicate API calls"""

    def __init__(self):
        self.redis_client = None
        self.use_redis = False
        self.cache_ttl = 3600
        self.local_cache = {}

        try:
            import redis
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True
            )
            self.redis_client.ping()
            self.use_redis = True
        except Exception:
            pass

    def _get_cache_key(self, scenario: str) -> str:
        normalized = ' '.join(scenario.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def get(self, scenario: str) -> Optional[Dict[str, Any]]:
        key = self._get_cache_key(scenario)

        if self.use_redis:
            cached = self.redis_client.get(key)
            return json.loads(cached) if cached else None
        else:
            cached = self.local_cache.get(key)
            if cached and datetime.now() < cached['expires']:
                return cached['data']
        return None

    def set(self, scenario: str, result: Dict[str, Any]):
        key = self._get_cache_key(scenario)
        expires = datetime.now() + timedelta(seconds=self.cache_ttl)

        if self.use_redis:
            self.redis_client.setex(key, self.cache_ttl, json.dumps(result))
        else:
            self.local_cache[key] = {'data': result, 'expires': expires}

    def clear(self):
        self.local_cache.clear()
        if self.use_redis:
            self.redis_client.flushdb()
