import hashlib
import time
from database import cache_get, cache_set, cache_delete, cache_stats_get, cache_stats_increment_hit, cache_stats_increment_miss, usage_log
from validators import validate_text, sanitize_text
from config import CACHE_MAX_RESPONSE_LENGTH
from logger import log_layer, log_error


def _hash(text):
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()[:32]


def check_cache(question, api_key):
    log_layer("flux", "check_cache", api_key)
    if not question:
        return {"hit": False, "layer": "FLUX"}
    valid, err = validate_text(question, field_name="question")
    if not valid:
        return {"hit": False, "layer": "FLUX"}
    usage_log(api_key, "flux", "check_cache")
    qhash = _hash(question)
    cached = cache_get(qhash)
    if cached:
        cache_stats_increment_hit(api_key)
        return {"hit": True, "response": cached, "speed_ms": 0, "source": "cache", "layer": "FLUX"}
    cache_stats_increment_miss(api_key)
    return {"hit": False, "layer": "FLUX"}


def store_cache(question, response, api_key):
    log_layer("flux", "store_cache", api_key)
    if not question or not response:
        return {"status": "error", "message": "question and response required", "layer": "FLUX"}
    valid, err = validate_text(question, field_name="question")
    if not valid:
        return {"status": "error", "message": err, "layer": "FLUX"}
    if len(response) > CACHE_MAX_RESPONSE_LENGTH:
        return {"status": "skipped", "reason": "response too large to cache", "layer": "FLUX"}
    usage_log(api_key, "flux", "store_cache")
    qhash = _hash(question)
    cache_set(qhash, response)
    return {"status": "cached", "hash": qhash, "layer": "FLUX"}


def invalidate_cache(question, api_key):
    log_layer("flux", "invalidate", api_key)
    if not question:
        return {"status": "error", "message": "question required", "layer": "FLUX"}
    usage_log(api_key, "flux", "invalidate")
    qhash = _hash(question)
    success = cache_delete(qhash)
    return {"status": "invalidated" if success else "not_found", "hash": qhash, "layer": "FLUX"}


def get_stats(api_key):
    stats = cache_stats_get(api_key)
    hit_count = stats.get("hit_count", 0)
    miss_count = stats.get("miss_count", 0)
    total = hit_count + miss_count
    hit_rate = round((hit_count / total) * 100, 1) if total > 0 else 0
    return {"total_cache_hits": hit_count, "total_cache_misses": miss_count, "hit_rate_percent": hit_rate, "total_requests": total, "layer": "FLUX"}


def benchmark(api_key):
    start = time.time()
    test_hash = _hash("kronyx benchmark test question")
    _ = cache_get(test_hash)
    duration_ms = round((time.time() - start) * 1000, 2)
    return {"cache_lookup_ms": duration_ms, "status": "fast" if duration_ms < 100 else "slow", "layer": "FLUX"}


def check_and_store(question, response_generator_result, api_key):
    log_layer("flux", "check_and_store", api_key)
    cached = check_cache(question, api_key)
    if cached.get("hit"):
        return {"served_from_cache": True, "response": cached["response"], "layer": "FLUX"}
    if response_generator_result:
        store_cache(question, str(response_generator_result), api_key)
    return {"served_from_cache": False, "response": response_generator_result, "layer": "FLUX"}


def get_cache_health():
    start = time.time()
    try:
        test_hash = _hash("health_check_test")
        cache_set(test_hash, "health_check_value")
        result = cache_get(test_hash)
        cache_delete(test_hash)
        duration_ms = round((time.time() - start) * 1000, 2)
        working = result == "health_check_value"
        return {"status": "healthy" if working else "degraded", "response_ms": duration_ms, "layer": "FLUX"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "layer": "FLUX"}


def warm_cache(questions_and_responses, api_key):
    log_layer("flux", "warm_cache", api_key)
    if not isinstance(questions_and_responses, list):
        return {"status": "error", "message": "must be a list of objects with question and response", "layer": "FLUX"}
    if len(questions_and_responses) > 100:
        return {"status": "error", "message": "max 100 items per warm operation", "layer": "FLUX"}
    cached_count = 0
    skipped_count = 0
    for item in questions_and_responses:
        if not isinstance(item, dict):
            skipped_count += 1
            continue
        question = item.get("question", "")
        response = item.get("response", "")
        if not question or not response:
            skipped_count += 1
            continue
        result = store_cache(question, response, api_key)
        if result.get("status") == "cached":
            cached_count += 1
        else:
            skipped_count += 1
    usage_log(api_key, "flux", "warm_cache")
    return {"status": "complete", "cached": cached_count, "skipped": skipped_count, "layer": "FLUX"}
