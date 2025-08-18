from flask import Flask
from flask_caching import Cache
cache = Cache()

def init_cache(flask_app):
     flask_app.config.setdefault("CACHE_TYPE", "SimpleCache")
     flask_app.config.setdefault("CACHE_DEFAULT_TIMEOUT", 60 * 60)  # 15 min    
     flask_app.config.setdefault("CACHE_THRESHOLD", 5000)
     cache.init_app(flask_app)