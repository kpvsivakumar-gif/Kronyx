from typing import Optional
from database import (
    memory_insert, memory_search, memory_search_all_users,
    memory_delete, memory_delete_by_user, memory_get_all,
    memory_get_recent, memory_count_active, memory_count_by_user,
    memory_stats_get, memory_stats_increment, memory_stats_increment_deleted,
    usage_log, interaction_log
)
from validators import validate_memory_content, validate_user_id, validate_query, validate_limit, sanitize_text
from logger import log_layer, log_error


def remember(content, user_id, api_key, tags=None):
    log_layer("memex", "remember", api_key)
    valid, err = validate_memory_content(content)
    if not valid:
        return {"status": "error", "message": err, "layer": "MEMEX"}
    valid, err = validate_user_id(user_id)
    if not valid:
        return {"status": "error", "message": err, "layer": "MEMEX"}
    content_clean = sanitize_text(content)
    user_id_clean = sanitize_text(user_id)
    if tags and isinstance(tags, list):
        tag_str = " [TAGS:" + ",".join(str(t) for t in tags[:10]) + "]"
        content_with_tags = content_clean + tag_str
    else:
        content_with_tags = content_clean
    result = memory_insert(content_with_tags, user_id_clean, api_key)
    if "error" in result:
        return {"status": "error", "message": "failed to store memory", "layer": "MEMEX"}
    memory_stats_increment(api_key)
    usage_log(api_key, "memex", "remember")
    interaction_log(api_key, user_id_clean, "memex", content_clean[:100], "stored")
    preview = content_clean[:100] + "..." if len(content_clean) > 100 else content_clean
    return {"status": "stored", "id": result.get("id", ""), "preview": preview, "user_id": user_id_clean, "layer": "MEMEX"}


def recall(query, user_id, api_key, limit=5):
    log_layer("memex", "recall", api_key)
    valid, err = validate_query(query)
    if not valid:
        return {"status": "error", "message": err, "layer": "MEMEX"}
    valid, err = validate_user_id(user_id)
    if not valid:
        return {"status": "error", "message": err, "layer": "MEMEX"}
    limit = validate_limit(limit)
    results = memory_search(sanitize_text(query), sanitize_text(user_id), api_key, limit)
    usage_log(api_key, "memex", "recall")
    return {"status": "success", "memories": results, "count": len(results), "query": query, "user_id": user_id, "layer": "MEMEX"}


def recall_global(query, api_key, limit=10):
    log_layer("memex", "recall_global", api_key)
    valid, err = validate_query(query)
    if not valid:
        return {"status": "error", "message": err, "layer": "MEMEX"}
    limit = validate_limit(limit, max_limit=20)
    results = memory_search_all_users(sanitize_text(query), api_key, limit)
    usage_log(api_key, "memex", "recall_global")
    return {"status": "success", "memories": results, "count": len(results), "query": query, "scope": "all_users", "layer": "MEMEX"}


def forget(memory_id, api_key):
    log_layer("memex", "forget", api_key)
    if not memory_id:
        return {"status": "error", "message": "memory_id required", "layer": "MEMEX"}
    success = memory_delete(memory_id, api_key)
    if success:
        memory_stats_increment_deleted(api_key)
    usage_log(api_key, "memex", "forget")
    if success:
        return {"status": "deleted", "id": memory_id, "layer": "MEMEX"}
    return {"status": "error", "message": "memory not found or already deleted", "layer": "MEMEX"}


def forget_user(user_id, api_key):
    log_layer("memex", "forget_user", api_key)
    valid, err = validate_user_id(user_id)
    if not valid:
        return {"status": "error", "message": err, "layer": "MEMEX"}
    count_before = memory_count_by_user(api_key, user_id)
    success = memory_delete_by_user(user_id, api_key)
    usage_log(api_key, "memex", "forget_user")
    return {"status": "deleted" if success else "error", "user_id": user_id, "deleted_count": count_before, "layer": "MEMEX"}


def get_all(api_key, user_id=None):
    log_layer("memex", "get_all", api_key)
    memories = memory_get_all(api_key, user_id)
    stats = memory_stats_get(api_key)
    active = memory_count_active(api_key)
    usage_log(api_key, "memex", "get_all")
    return {
        "status": "success",
        "memories": memories,
        "active_count": active,
        "total_ever": stats.get("total_ever", 0),
        "deleted_count": stats.get("deleted_count", 0),
        "layer": "MEMEX"
    }


def get_recent(api_key, limit=20):
    log_layer("memex", "get_recent", api_key)
    limit = validate_limit(limit, max_limit=50)
    memories = memory_get_recent(api_key, limit)
    usage_log(api_key, "memex", "get_recent")
    return {"status": "success", "memories": memories, "count": len(memories), "layer": "MEMEX"}


def get_stats(api_key):
    stats = memory_stats_get(api_key)
    active = memory_count_active(api_key)
    return {
        "active": active,
        "total_ever": stats.get("total_ever", 0),
        "deleted": stats.get("deleted_count", 0),
        "auto_delete_days": 90,
        "storage_used_estimate": f"{active * 0.5:.1f} KB",
        "layer": "MEMEX"
    }


def get_user_memory_count(api_key, user_id):
    log_layer("memex", "user_count", api_key)
    valid, err = validate_user_id(user_id)
    if not valid:
        return {"status": "error", "message": err, "layer": "MEMEX"}
    count = memory_count_by_user(api_key, user_id)
    return {"user_id": user_id, "memory_count": count, "layer": "MEMEX"}


def search_by_tag(tag, api_key, user_id=None, limit=10):
    log_layer("memex", "search_by_tag", api_key)
    if not tag:
        return {"status": "error", "message": "tag required", "layer": "MEMEX"}
    tag_query = f"TAGS:{tag}"
    if user_id:
        results = memory_search(tag_query, user_id, api_key, limit)
    else:
        results = memory_search_all_users(tag_query, api_key, limit)
    usage_log(api_key, "memex", "search_by_tag")
    return {"status": "success", "tag": tag, "memories": results, "count": len(results), "layer": "MEMEX"}


def memory_exists(content_preview, user_id, api_key):
    log_layer("memex", "exists", api_key)
    if not content_preview or not user_id:
        return {"exists": False, "layer": "MEMEX"}
    results = memory_search(content_preview[:50], user_id, api_key, 3)
    exists = len(results) > 0
    return {"exists": exists, "similar_count": len(results), "layer": "MEMEX"}


def get_memory_timeline(api_key, user_id, limit=30):
    log_layer("memex", "timeline", api_key)
    valid, err = validate_user_id(user_id)
    if not valid:
        return {"status": "error", "message": err, "layer": "MEMEX"}
    memories = memory_get_all(api_key, user_id)
    memories_sorted = sorted(memories, key=lambda x: x.get("created_at", ""), reverse=False)
    timeline = []
    for m in memories_sorted[:limit]:
        timeline.append({
            "id": m.get("id", ""),
            "content_preview": str(m.get("content", ""))[:80],
            "date": str(m.get("created_at", ""))[:10]
        })
    usage_log(api_key, "memex", "timeline")
    return {"status": "success", "user_id": user_id, "timeline": timeline, "total": len(timeline), "layer": "MEMEX"}


def bulk_remember(items, api_key):
    log_layer("memex", "bulk_remember", api_key)
    if not isinstance(items, list) or len(items) == 0:
        return {"status": "error", "message": "items must be a non-empty list", "layer": "MEMEX"}
    if len(items) > 50:
        return {"status": "error", "message": "maximum 50 items per bulk operation", "layer": "MEMEX"}
    stored = 0
    errors = 0
    ids = []
    for item in items:
        if not isinstance(item, dict):
            errors += 1
            continue
        content = item.get("content", "")
        user_id = item.get("user_id", "")
        if not content or not user_id:
            errors += 1
            continue
        valid_c, _ = validate_memory_content(content)
        valid_u, _ = validate_user_id(user_id)
        if not valid_c or not valid_u:
            errors += 1
            continue
        result = memory_insert(sanitize_text(content), sanitize_text(user_id), api_key)
        if "error" not in result:
            stored += 1
            memory_stats_increment(api_key)
            ids.append(result.get("id", ""))
        else:
            errors += 1
    usage_log(api_key, "memex", "bulk_remember")
    return {"status": "completed", "stored": stored, "errors": errors, "ids": ids, "layer": "MEMEX"}
