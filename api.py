from fastapi import APIRouter, Header, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from auth import validate_api_key, signup_user, login_user, change_password
from rate_limiter import check_rate_limit, get_usage_stats, get_reset_time
from database import user_update_key, user_get_by_email, admin_get_global_stats, user_get_all
from security import generate_api_key
from email_service import send_welcome, send_key_regenerated
from validators import validate_key_number
from notifications import get_notifications, mark_as_read, get_unread_count, clear_all_notifications
from export import export_all_data, export_memories_only, export_analytics_only, get_export_summary
from webhooks import register_webhook, get_webhooks, delete_webhook, fire_webhook, test_webhook, get_valid_events
from admin import get_global_stats, get_all_users, get_top_users_by_usage, get_system_health, delete_user_account, run_maintenance_task, get_usage_overview, get_layer_usage_overview, verify_admin_key
from layers.memex import remember, recall, recall_global, forget, forget_user, get_all, get_recent, get_stats as memex_stats, get_user_memory_count, search_by_tag, memory_exists, get_memory_timeline, bulk_remember
from layers.sentinel import check as sentinel_check, scan_input, check_batch, get_issues, get_live_feed, get_threat_by_type, analyze_response_quality, get_sentinel_dashboard
from layers.flux import check_cache, store_cache, invalidate_cache, get_stats as flux_stats, benchmark, check_and_store, get_cache_health, warm_cache
from layers.vault import scan as vault_scan, scan_batch, scan_url, get_security_report, get_threat_summary, check_api_key_security, get_blocked_patterns
from layers.atlas import translate, translate_batch, detect_language, auto_translate_response, get_supported_languages, get_language_info, get_translation_coverage
from layers.pulse import health_check, report_incident, resolve_incident, get_health_report, get_uptime_percentage, get_incident_history, heartbeat, get_performance_metrics, auto_recover
from layers.insight import track as insight_track, get_stats as insight_stats, get_user_stats, get_dashboard_data, get_usage_timeline, get_layer_performance, get_growth_metrics, get_ai_performance_summary, export_analytics
from layers.advanced import oracle_predict_intent, oracle_get_intent_history, oracle_analyze_pattern, genome_build_profile, genome_get_profile, genome_inject_personality, genome_generate_prompt, nexus_connect_source, nexus_fetch_url, nexus_add_knowledge, nexus_get_knowledge, nexus_fuse_knowledge, nexus_get_sources, echo_cross_check, echo_verify_factual, lens_analyze, lens_build_context_prompt, prima_process
from layers.impossible import duality_superpose, duality_evaluate_paradox, akasha_recognize_pattern, zero_analyze_absence, zero_detect_gaps, deep_process_meaning, apex_cultivate_emergence, babel_translate_domain, eternal_analyze_impact, infinite_process_paradox, infinite_hold_contradiction, abyss_detect_blind_spots, fractal_analyze_at_scale, origin_generate_first_principle
from layers.genesis_prime import process as genesis_process, understand as genesis_understand, generate_understanding_response, get_semantic_weight, analyze_conversation_depth

router = APIRouter()


def require_key(x_api_key: str = Header(...)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    user = validate_api_key(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    rate = check_rate_limit(x_api_key)
    if not rate["allowed"]:
        raise HTTPException(status_code=429, detail=f"Daily limit reached. Resets midnight UTC.")
    return user, x_api_key


class SignupBody(BaseModel):
    email: str
    password: str

class LoginBody(BaseModel):
    email: str
    password: str

class ChangePasswordBody(BaseModel):
    old_password: str
    new_password: str

class RememberBody(BaseModel):
    content: str
    user_id: str
    tags: Optional[List[str]] = None

class RecallBody(BaseModel):
    query: str
    user_id: str
    limit: Optional[int] = 5

class ForgetUserBody(BaseModel):
    user_id: str

class BulkRememberBody(BaseModel):
    items: List[dict]

class TagSearchBody(BaseModel):
    tag: str
    user_id: Optional[str] = None
    limit: Optional[int] = 10

class CheckBody(BaseModel):
    response: str

class BatchCheckBody(BaseModel):
    responses: List[str]

class ScanInputBody(BaseModel):
    message: str

class BatchScanBody(BaseModel):
    messages: List[str]

class ScanUrlBody(BaseModel):
    url: str

class CacheCheckBody(BaseModel):
    question: str

class CacheStoreBody(BaseModel):
    question: str
    response: str

class WarmCacheBody(BaseModel):
    items: List[dict]

class VaultScanBody(BaseModel):
    message: str

class TranslateBody(BaseModel):
    text: str
    target_language: str

class BatchTranslateBody(BaseModel):
    texts: List[str]
    target_language: str

class DetectLanguageBody(BaseModel):
    text: str

class IncidentBody(BaseModel):
    description: str
    severity: Optional[str] = "medium"

class InsightTrackBody(BaseModel):
    question: str
    response: str
    user_id: str
    response_time: Optional[float] = 0.0

class OracleBody(BaseModel):
    message: str
    user_id: str

class ConversationBody(BaseModel):
    messages: List[str]

class GenomeProfileBody(BaseModel):
    business_name: str
    business_type: str
    tone: Optional[str] = "professional"
    vocabulary: Optional[str] = "general"
    personality_traits: Optional[List[str]] = None
    preferred_words: Optional[List[str]] = None
    avoid_words: Optional[List[str]] = None

class InjectBody(BaseModel):
    response: str

class NexusSourceBody(BaseModel):
    source_type: str
    source_url: str
    name: Optional[str] = ""
    refresh_minutes: Optional[int] = 60

class NexusKnowledgeBody(BaseModel):
    content: str
    topic: str

class EchoCheckBody(BaseModel):
    response: str
    previous_responses: Optional[List[str]] = None

class EchoVerifyBody(BaseModel):
    statement: str
    context: str

class LensBody(BaseModel):
    message: str
    user_id: str
    history: Optional[List[str]] = None

class PrimaBody(BaseModel):
    text: str

class SuperposeBody(BaseModel):
    question: str
    possible_answers: List[str]
    context: Optional[str] = ""

class ParadoxBody(BaseModel):
    statement_a: str
    statement_b: str

class AkashaBody(BaseModel):
    text: str
    domain: str

class ZeroAbsenceBody(BaseModel):
    text: str
    context_type: str

class ZeroGapsBody(BaseModel):
    conversation: List[str]

class DeepBody(BaseModel):
    text: str

class ApexBody(BaseModel):
    problem: str
    iterations: Optional[int] = 3

class BabelBody(BaseModel):
    concept: str
    source_domain: str
    target_domain: str

class EternalBody(BaseModel):
    decision: str
    domain: str
    time_horizon_years: Optional[int] = 100

class InfiniteBody(BaseModel):
    statement: str

class ContradictionBody(BaseModel):
    position_a: str
    position_b: str
    context: Optional[str] = ""

class AbyssBody(BaseModel):
    text: str
    domain: str

class FractalBody(BaseModel):
    problem: str
    scale: str

class OriginBody(BaseModel):
    domain: str

class GenesisBody(BaseModel):
    text: str

class GenesisUnderstandBody(BaseModel):
    text: str
    context: Optional[str] = ""

class SemanticWeightBody(BaseModel):
    word: str

class EvolveTrackBody(BaseModel):
    question: str
    response: str
    score: int

class WebhookBody(BaseModel):
    url: str
    events: List[str]

class WebhookTestBody(BaseModel):
    url: str

class NotificationReadBody(BaseModel):
    notification_id: str

class AdminTaskBody(BaseModel):
    task_name: str
    admin_key: str

class CompleteFlowBody(BaseModel):
    message: str
    user_id: str
    response: Optional[str] = None
    target_language: Optional[str] = None


@router.post("/v1/account/signup")
async def signup(body: SignupBody):
    result = signup_user(body.email, body.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    send_welcome(body.email, result["api_key_1"], result["api_key_2"])
    return {"status": "created", "email": body.email, "api_key_1": result["api_key_1"], "api_key_2": result["api_key_2"], "access_token": result["access_token"], "token_type": "bearer", "message": "Welcome to KRONYX. 2 API keys created.", "disclaimer": "You are responsible for all usage under your API keys. Never share publicly."}


@router.post("/v1/account/login")
async def login(body: LoginBody, request: Request):
    ip = request.client.host if request.client else "unknown"
    result = login_user(body.email, body.password, ip)
    if not result["success"]:
        code = 429 if result.get("blocked") else 401
        raise HTTPException(status_code=code, detail=result["error"])
    return {"status": "logged_in", "email": result["user"]["email"], "api_key_1": result["user"]["api_key_1"], "api_key_2": result["user"]["api_key_2"], "access_token": result["access_token"], "token_type": "bearer"}


@router.post("/v1/account/regenerate/{key_number}")
async def regenerate_key(key_number: int, auth=Depends(require_key)):
    user, api_key = auth
    valid, err = validate_key_number(key_number)
    if not valid:
        raise HTTPException(status_code=400, detail=err)
    new_key = generate_api_key()
    success = user_update_key(user["id"], key_number, new_key)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to regenerate key")
    send_key_regenerated(user["email"], new_key, key_number)
    return {"status": "regenerated", "key_number": key_number, "new_key": new_key, "warning": "Old key permanently deactivated. Update your code immediately.", "coming_soon": "multiple_api_keys"}


@router.post("/v1/account/change-password")
async def change_pwd(body: ChangePasswordBody, auth=Depends(require_key)):
    user, api_key = auth
    result = change_password(user["id"], body.old_password, body.new_password, user["password"])
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/v1/account/dashboard")
async def dashboard(auth=Depends(require_key)):
    user, api_key = auth
    return {"email": user["email"], "api_key_1": user["api_key_1"], "api_key_2": user["api_key_2"], "memex": memex_stats(api_key), "vault_summary": get_threat_summary(api_key), "insight": get_dashboard_data(api_key), "pulse": health_check(), "usage": get_usage_stats(api_key), "flux": flux_stats(api_key), "more_keys": "coming_soon", "team_members": "coming_soon", "pro_plan": "coming_soon"}


@router.get("/v1/account/usage")
async def usage(auth=Depends(require_key)):
    user, api_key = auth
    stats = get_usage_stats(api_key)
    reset = get_reset_time()
    stats["reset_info"] = reset
    return stats


@router.post("/v1/memex/remember")
async def api_remember(body: RememberBody, auth=Depends(require_key)):
    user, key = auth
    return remember(body.content, body.user_id, key, body.tags)


@router.post("/v1/memex/recall")
async def api_recall(body: RecallBody, auth=Depends(require_key)):
    user, key = auth
    return recall(body.query, body.user_id, key, body.limit or 5)


@router.post("/v1/memex/recall-global")
async def api_recall_global(body: CacheCheckBody, auth=Depends(require_key)):
    user, key = auth
    return recall_global(body.question, key)


@router.delete("/v1/memex/forget/{memory_id}")
async def api_forget(memory_id: str, auth=Depends(require_key)):
    user, key = auth
    return forget(memory_id, key)


@router.post("/v1/memex/forget-user")
async def api_forget_user(body: ForgetUserBody, auth=Depends(require_key)):
    user, key = auth
    return forget_user(body.user_id, key)


@router.get("/v1/memex/all")
async def api_all_memories(user_id: Optional[str] = None, auth=Depends(require_key)):
    user, key = auth
    return get_all(key, user_id)


@router.get("/v1/memex/recent")
async def api_recent_memories(limit: Optional[int] = 20, auth=Depends(require_key)):
    user, key = auth
    return get_recent(key, limit or 20)


@router.get("/v1/memex/stats")
async def api_memory_stats(auth=Depends(require_key)):
    user, key = auth
    return memex_stats(key)


@router.get("/v1/memex/user-count/{user_id}")
async def api_user_memory_count(user_id: str, auth=Depends(require_key)):
    user, key = auth
    return get_user_memory_count(key, user_id)


@router.post("/v1/memex/search-tag")
async def api_search_tag(body: TagSearchBody, auth=Depends(require_key)):
    user, key = auth
    return search_by_tag(body.tag, key, body.user_id, body.limit or 10)


@router.get("/v1/memex/timeline/{user_id}")
async def api_memory_timeline(user_id: str, limit: Optional[int] = 30, auth=Depends(require_key)):
    user, key = auth
    return get_memory_timeline(key, user_id, limit or 30)


@router.post("/v1/memex/bulk")
async def api_bulk_remember(body: BulkRememberBody, auth=Depends(require_key)):
    user, key = auth
    return bulk_remember(body.items, key)


@router.post("/v1/sentinel/check")
async def api_sentinel_check(body: CheckBody, auth=Depends(require_key)):
    user, key = auth
    return sentinel_check(body.response, key)


@router.post("/v1/sentinel/check-batch")
async def api_sentinel_batch(body: BatchCheckBody, auth=Depends(require_key)):
    user, key = auth
    return check_batch(body.responses, key)


@router.post("/v1/sentinel/scan")
async def api_sentinel_scan(body: ScanInputBody, auth=Depends(require_key)):
    user, key = auth
    return scan_input(body.message, key)


@router.get("/v1/sentinel/issues")
async def api_sentinel_issues(auth=Depends(require_key)):
    user, key = auth
    return get_issues(key)


@router.get("/v1/sentinel/feed")
async def api_sentinel_feed(auth=Depends(require_key)):
    user, key = auth
    return get_live_feed(key)


@router.get("/v1/sentinel/threat-type/{threat_type}")
async def api_threat_by_type(threat_type: str, auth=Depends(require_key)):
    user, key = auth
    return get_threat_by_type(key, threat_type)


@router.post("/v1/sentinel/quality")
async def api_response_quality(body: CheckBody, auth=Depends(require_key)):
    user, key = auth
    return analyze_response_quality(body.response, key)


@router.get("/v1/sentinel/dashboard")
async def api_sentinel_dashboard(auth=Depends(require_key)):
    user, key = auth
    return get_sentinel_dashboard(key)


@router.post("/v1/flux/check")
async def api_flux_check(body: CacheCheckBody, auth=Depends(require_key)):
    user, key = auth
    return check_cache(body.question, key)


@router.post("/v1/flux/store")
async def api_flux_store(body: CacheStoreBody, auth=Depends(require_key)):
    user, key = auth
    return store_cache(body.question, body.response, key)


@router.post("/v1/flux/invalidate")
async def api_flux_invalidate(body: CacheCheckBody, auth=Depends(require_key)):
    user, key = auth
    return invalidate_cache(body.question, key)


@router.get("/v1/flux/stats")
async def api_flux_stats(auth=Depends(require_key)):
    user, key = auth
    return flux_stats(key)


@router.get("/v1/flux/benchmark")
async def api_flux_benchmark(auth=Depends(require_key)):
    user, key = auth
    return benchmark(key)


@router.get("/v1/flux/health")
async def api_cache_health():
    return get_cache_health()


@router.post("/v1/flux/warm")
async def api_flux_warm(body: WarmCacheBody, auth=Depends(require_key)):
    user, key = auth
    return warm_cache(body.items, key)


@router.post("/v1/vault/scan")
async def api_vault_scan(body: VaultScanBody, auth=Depends(require_key)):
    user, key = auth
    return vault_scan(body.message, key)


@router.post("/v1/vault/scan-batch")
async def api_vault_batch(body: BatchScanBody, auth=Depends(require_key)):
    user, key = auth
    return scan_batch(body.messages, key)


@router.post("/v1/vault/scan-url")
async def api_vault_url(body: ScanUrlBody, auth=Depends(require_key)):
    user, key = auth
    return scan_url(body.url, key)


@router.get("/v1/vault/report")
async def api_vault_report(auth=Depends(require_key)):
    user, key = auth
    return get_security_report(key)


@router.get("/v1/vault/summary")
async def api_vault_summary(auth=Depends(require_key)):
    user, key = auth
    return get_threat_summary(key)


@router.get("/v1/vault/patterns")
async def api_vault_patterns():
    return get_blocked_patterns()


@router.post("/v1/atlas/translate")
async def api_atlas_translate(body: TranslateBody, auth=Depends(require_key)):
    user, key = auth
    return translate(body.text, body.target_language, key)


@router.post("/v1/atlas/translate-batch")
async def api_atlas_batch(body: BatchTranslateBody, auth=Depends(require_key)):
    user, key = auth
    return translate_batch(body.texts, body.target_language, key)


@router.post("/v1/atlas/detect")
async def api_atlas_detect(body: DetectLanguageBody, auth=Depends(require_key)):
    user, key = auth
    return detect_language(body.text)


@router.post("/v1/atlas/auto")
async def api_atlas_auto(body: TranslateBody, auth=Depends(require_key)):
    user, key = auth
    return auto_translate_response(body.text, body.target_language, key)


@router.get("/v1/atlas/languages")
async def api_atlas_languages():
    return get_supported_languages()


@router.get("/v1/atlas/language/{code}")
async def api_language_info(code: str):
    return get_language_info(code)


@router.get("/v1/atlas/coverage")
async def api_translation_coverage():
    return get_translation_coverage()


@router.get("/v1/pulse/health")
async def api_pulse_health():
    return health_check()


@router.post("/v1/pulse/incident")
async def api_pulse_incident(body: IncidentBody, auth=Depends(require_key)):
    user, key = auth
    return report_incident(key, body.description, body.severity or "medium")


@router.post("/v1/pulse/resolve/{incident_id}")
async def api_pulse_resolve(incident_id: str, auth=Depends(require_key)):
    user, key = auth
    return resolve_incident(incident_id, key)


@router.get("/v1/pulse/report")
async def api_pulse_report(auth=Depends(require_key)):
    user, key = auth
    return get_health_report(key)


@router.get("/v1/pulse/uptime")
async def api_pulse_uptime(auth=Depends(require_key)):
    user, key = auth
    return get_uptime_percentage(key)


@router.get("/v1/pulse/incidents")
async def api_pulse_incidents(include_resolved: Optional[bool] = True, auth=Depends(require_key)):
    user, key = auth
    return get_incident_history(key, include_resolved if include_resolved is not None else True)


@router.get("/v1/pulse/heartbeat")
async def api_pulse_heartbeat(auth=Depends(require_key)):
    user, key = auth
    return heartbeat(key)


@router.get("/v1/pulse/metrics")
async def api_pulse_metrics(auth=Depends(require_key)):
    user, key = auth
    return get_performance_metrics(key)


@router.post("/v1/pulse/auto-recover")
async def api_pulse_auto_recover(auth=Depends(require_key)):
    user, key = auth
    return auto_recover(key)


@router.post("/v1/insight/track")
async def api_insight_track(body: InsightTrackBody, auth=Depends(require_key)):
    user, key = auth
    return insight_track(body.question, body.response, body.user_id, key, body.response_time or 0.0)


@router.get("/v1/insight/stats")
async def api_insight_stats(auth=Depends(require_key)):
    user, key = auth
    return insight_stats(key)


@router.get("/v1/insight/user/{user_id}")
async def api_insight_user(user_id: str, auth=Depends(require_key)):
    user, key = auth
    return get_user_stats(key, user_id)


@router.get("/v1/insight/dashboard")
async def api_insight_dashboard(auth=Depends(require_key)):
    user, key = auth
    return get_dashboard_data(key)


@router.get("/v1/insight/timeline")
async def api_insight_timeline(days: Optional[int] = 30, auth=Depends(require_key)):
    user, key = auth
    return get_usage_timeline(key, days or 30)


@router.get("/v1/insight/layer-performance")
async def api_layer_performance(auth=Depends(require_key)):
    user, key = auth
    return get_layer_performance(key)


@router.get("/v1/insight/growth")
async def api_insight_growth(auth=Depends(require_key)):
    user, key = auth
    return get_growth_metrics(key)


@router.get("/v1/insight/ai-performance")
async def api_ai_performance(auth=Depends(require_key)):
    user, key = auth
    return get_ai_performance_summary(key)


@router.get("/v1/insight/export")
async def api_insight_export(auth=Depends(require_key)):
    user, key = auth
    return export_analytics(key)


@router.post("/v1/oracle/predict")
async def api_oracle_predict(body: OracleBody, auth=Depends(require_key)):
    user, key = auth
    return oracle_predict_intent(body.message, body.user_id, key)


@router.get("/v1/oracle/history/{user_id}")
async def api_oracle_history(user_id: str, auth=Depends(require_key)):
    user, key = auth
    return oracle_get_intent_history(key, user_id)


@router.post("/v1/oracle/analyze")
async def api_oracle_analyze(body: ConversationBody, auth=Depends(require_key)):
    user, key = auth
    return oracle_analyze_pattern(body.messages, key)


@router.post("/v1/genome/build")
async def api_genome_build(body: GenomeProfileBody, auth=Depends(require_key)):
    user, key = auth
    return genome_build_profile(body.business_name, body.business_type, body.tone or "professional", body.vocabulary or "general", body.personality_traits or [], body.preferred_words or [], body.avoid_words or [], key)


@router.get("/v1/genome/profile")
async def api_genome_profile(auth=Depends(require_key)):
    user, key = auth
    return genome_get_profile(key)


@router.post("/v1/genome/inject")
async def api_genome_inject(body: InjectBody, auth=Depends(require_key)):
    user, key = auth
    return genome_inject_personality(body.response, key)


@router.get("/v1/genome/prompt")
async def api_genome_prompt(auth=Depends(require_key)):
    user, key = auth
    return genome_generate_prompt(key)


@router.post("/v1/nexus/connect")
async def api_nexus_connect(body: NexusSourceBody, auth=Depends(require_key)):
    user, key = auth
    return nexus_connect_source(body.source_type, body.source_url, key, body.name or "", body.refresh_minutes or 60)


@router.post("/v1/nexus/fetch")
async def api_nexus_fetch(body: CacheCheckBody, auth=Depends(require_key)):
    user, key = auth
    return nexus_fetch_url(body.question, key)


@router.post("/v1/nexus/knowledge")
async def api_nexus_add(body: NexusKnowledgeBody, auth=Depends(require_key)):
    user, key = auth
    return nexus_add_knowledge(body.content, body.topic, key)


@router.get("/v1/nexus/knowledge/{topic}")
async def api_nexus_get(topic: str, auth=Depends(require_key)):
    user, key = auth
    return nexus_get_knowledge(topic, key)


@router.post("/v1/nexus/fuse")
async def api_nexus_fuse(body: CacheCheckBody, auth=Depends(require_key)):
    user, key = auth
    return nexus_fuse_knowledge(body.question, key)


@router.get("/v1/nexus/sources")
async def api_nexus_sources(auth=Depends(require_key)):
    user, key = auth
    return nexus_get_sources(key)


@router.post("/v1/echo/check")
async def api_echo_check(body: EchoCheckBody, auth=Depends(require_key)):
    user, key = auth
    return echo_cross_check(body.response, body.previous_responses or [], key)


@router.post("/v1/echo/verify")
async def api_echo_verify(body: EchoVerifyBody, auth=Depends(require_key)):
    user, key = auth
    return echo_verify_factual(body.statement, body.context, key)


@router.post("/v1/lens/analyze")
async def api_lens_analyze(body: LensBody, auth=Depends(require_key)):
    user, key = auth
    return lens_analyze(body.message, body.user_id, key, body.history)


@router.post("/v1/lens/context")
async def api_lens_context(body: LensBody, auth=Depends(require_key)):
    user, key = auth
    return lens_build_context_prompt(body.message, body.user_id, key)


@router.post("/v1/prima/process")
async def api_prima_process(body: PrimaBody, auth=Depends(require_key)):
    user, key = auth
    return prima_process(body.text, key)


@router.post("/v1/duality/superpose")
async def api_duality_superpose(body: SuperposeBody, auth=Depends(require_key)):
    user, key = auth
    return duality_superpose(body.question, body.possible_answers, body.context or "", key)


@router.post("/v1/duality/paradox")
async def api_duality_paradox(body: ParadoxBody, auth=Depends(require_key)):
    user, key = auth
    return duality_evaluate_paradox(body.statement_a, body.statement_b, key)


@router.post("/v1/akasha/recognize")
async def api_akasha_recognize(body: AkashaBody, auth=Depends(require_key)):
    user, key = auth
    return akasha_recognize_pattern(body.text, body.domain, key)


@router.post("/v1/zero/absence")
async def api_zero_absence(body: ZeroAbsenceBody, auth=Depends(require_key)):
    user, key = auth
    return zero_analyze_absence(body.text, body.context_type, key)


@router.post("/v1/zero/gaps")
async def api_zero_gaps(body: ZeroGapsBody, auth=Depends(require_key)):
    user, key = auth
    return zero_detect_gaps(body.conversation, key)


@router.post("/v1/deep/meaning")
async def api_deep_meaning(body: DeepBody, auth=Depends(require_key)):
    user, key = auth
    return deep_process_meaning(body.text, key)


@router.post("/v1/apex/cultivate")
async def api_apex_cultivate(body: ApexBody, auth=Depends(require_key)):
    user, key = auth
    return apex_cultivate_emergence(body.problem, key, body.iterations or 3)


@router.post("/v1/babel/translate")
async def api_babel_translate(body: BabelBody, auth=Depends(require_key)):
    user, key = auth
    return babel_translate_domain(body.concept, body.source_domain, body.target_domain, key)


@router.post("/v1/eternal/impact")
async def api_eternal_impact(body: EternalBody, auth=Depends(require_key)):
    user, key = auth
    return eternal_analyze_impact(body.decision, body.domain, key, body.time_horizon_years or 100)


@router.post("/v1/infinite/paradox")
async def api_infinite_paradox(body: InfiniteBody, auth=Depends(require_key)):
    user, key = auth
    return infinite_process_paradox(body.statement, key)


@router.post("/v1/infinite/hold")
async def api_infinite_hold(body: ContradictionBody, auth=Depends(require_key)):
    user, key = auth
    return infinite_hold_contradiction(body.position_a, body.position_b, body.context or "", key)


@router.post("/v1/abyss/blindspots")
async def api_abyss_blindspots(body: AbyssBody, auth=Depends(require_key)):
    user, key = auth
    return abyss_detect_blind_spots(body.text, body.domain, key)


@router.post("/v1/fractal/scale")
async def api_fractal_scale(body: FractalBody, auth=Depends(require_key)):
    user, key = auth
    return fractal_analyze_at_scale(body.problem, body.scale, key)


@router.post("/v1/origin/generate")
async def api_origin_generate(body: OriginBody, auth=Depends(require_key)):
    user, key = auth
    return origin_generate_first_principle(body.domain, key)


@router.post("/v1/genesis/process")
async def api_genesis_process(body: GenesisBody, auth=Depends(require_key)):
    user, key = auth
    return genesis_process(body.text, key)


@router.post("/v1/genesis/understand")
async def api_genesis_understand(body: GenesisUnderstandBody, auth=Depends(require_key)):
    user, key = auth
    return genesis_understand(body.text, body.context or "", key)


@router.post("/v1/genesis/respond")
async def api_genesis_respond(body: GenesisBody, auth=Depends(require_key)):
    user, key = auth
    return generate_understanding_response(body.text, key)


@router.post("/v1/genesis/weight")
async def api_genesis_weight(body: SemanticWeightBody, auth=Depends(require_key)):
    user, key = auth
    return get_semantic_weight(body.word, key)


@router.post("/v1/genesis/conversation-depth")
async def api_genesis_depth(body: ConversationBody, auth=Depends(require_key)):
    user, key = auth
    return analyze_conversation_depth(body.messages, key)


@router.post("/v1/evolve/track")
async def api_evolve_track(body: EvolveTrackBody, auth=Depends(require_key)):
    from database import evolve_log, usage_log
    user, key = auth
    if not (0 <= body.score <= 100):
        raise HTTPException(status_code=400, detail="score must be 0 to 100")
    evolve_log(key, body.question, body.response, body.score)
    usage_log(key, "evolve", "track")
    return {"status": "tracked", "score": body.score, "layer": "EVOLVE"}


@router.get("/v1/evolve/performance")
async def api_evolve_performance(auth=Depends(require_key)):
    from database import evolve_get_performance, usage_log
    user, key = auth
    usage_log(key, "evolve", "performance")
    perf = evolve_get_performance(key)
    avg = perf.get("average_score", 0)
    grade = "A" if avg >= 90 else "B" if avg >= 80 else "C" if avg >= 70 else "D"
    return {"average_score": avg, "grade": grade, "total_tracked": perf.get("total_tracked", 0), "trend": perf.get("trend", "no_data"), "layer": "EVOLVE"}


@router.post("/v1/webhooks/register")
async def api_webhook_register(body: WebhookBody, auth=Depends(require_key)):
    user, key = auth
    return register_webhook(key, body.url, body.events)


@router.get("/v1/webhooks")
async def api_webhook_list(auth=Depends(require_key)):
    user, key = auth
    return get_webhooks(key)


@router.delete("/v1/webhooks/{webhook_id}")
async def api_webhook_delete(webhook_id: str, auth=Depends(require_key)):
    user, key = auth
    return delete_webhook(webhook_id, key)


@router.post("/v1/webhooks/test")
async def api_webhook_test(body: WebhookTestBody, auth=Depends(require_key)):
    user, key = auth
    return test_webhook(key, body.url)


@router.get("/v1/webhooks/events")
async def api_webhook_events():
    return get_valid_events()


@router.get("/v1/notifications")
async def api_get_notifications(unread_only: Optional[bool] = False, auth=Depends(require_key)):
    user, key = auth
    return get_notifications(key, unread_only or False)


@router.post("/v1/notifications/read")
async def api_mark_read(body: NotificationReadBody, auth=Depends(require_key)):
    user, key = auth
    return mark_as_read(body.notification_id, key)


@router.get("/v1/notifications/unread-count")
async def api_unread_count(auth=Depends(require_key)):
    user, key = auth
    return get_unread_count(key)


@router.post("/v1/notifications/clear")
async def api_clear_notifications(auth=Depends(require_key)):
    user, key = auth
    return clear_all_notifications(key)


@router.get("/v1/export/all")
async def api_export_all(auth=Depends(require_key)):
    user, key = auth
    return export_all_data(key)


@router.get("/v1/export/memories")
async def api_export_memories(auth=Depends(require_key)):
    user, key = auth
    return export_memories_only(key)


@router.get("/v1/export/analytics")
async def api_export_analytics(auth=Depends(require_key)):
    user, key = auth
    return export_analytics_only(key)


@router.get("/v1/export/summary")
async def api_export_summary(auth=Depends(require_key)):
    user, key = auth
    return get_export_summary(key)


@router.get("/v1/admin/stats", include_in_schema=False)
async def api_admin_stats(x_admin_key: str = Header(...)):
    if not verify_admin_key(x_admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return get_global_stats()


@router.get("/v1/admin/users", include_in_schema=False)
async def api_admin_users(x_admin_key: str = Header(...)):
    if not verify_admin_key(x_admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return get_all_users()


@router.get("/v1/admin/top-users", include_in_schema=False)
async def api_admin_top_users(x_admin_key: str = Header(...)):
    if not verify_admin_key(x_admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return get_top_users_by_usage()


@router.get("/v1/admin/system-health", include_in_schema=False)
async def api_admin_health(x_admin_key: str = Header(...)):
    if not verify_admin_key(x_admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return get_system_health()


@router.get("/v1/admin/usage-overview", include_in_schema=False)
async def api_admin_usage(x_admin_key: str = Header(...)):
    if not verify_admin_key(x_admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return get_usage_overview()


@router.get("/v1/admin/layer-usage", include_in_schema=False)
async def api_admin_layer_usage(x_admin_key: str = Header(...)):
    if not verify_admin_key(x_admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return get_layer_usage_overview()


@router.post("/v1/admin/task", include_in_schema=False)
async def api_admin_task(body: AdminTaskBody):
    if not verify_admin_key(body.admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return run_maintenance_task(body.task_name, body.admin_key)


@router.post("/v1/flow/complete")
async def api_complete_flow(body: CompleteFlowBody, auth=Depends(require_key)):
    user, key = auth
    results = {}
    vault_result = vault_scan(body.message, key)
    results["vault"] = vault_result
    if not vault_result.get("is_safe"):
        return {"blocked": True, "reason": vault_result.get("threat"), "results": results}
    cached = check_cache(body.message, key)
    results["flux"] = cached
    if cached.get("hit"):
        return {"blocked": False, "cache_hit": True, "response": cached.get("response"), "results": results}
    memories = recall(body.message, body.user_id, key, 3)
    results["memex"] = memories
    oracle = oracle_predict_intent(body.message, body.user_id, key)
    results["oracle"] = oracle
    lens = lens_build_context_prompt(body.message, body.user_id, key)
    results["lens"] = lens
    genesis = genesis_process(body.message, key)
    results["genesis_prime"] = {"coherence_score": genesis.get("coherence_score"), "understanding_level": genesis.get("understanding_level")}
    if body.response:
        sentinel = sentinel_check(body.response, key)
        results["sentinel"] = sentinel
        if sentinel.get("is_safe"):
            remember(f"User: {body.message[:100]}", body.user_id, key)
            store_cache(body.message, body.response, key)
            insight_track(body.message, body.response, body.user_id, key, 0.0)
        if body.target_language and body.target_language != "en":
            translated = translate(body.response, body.target_language, key)
            results["atlas"] = translated
    return {"blocked": False, "cache_hit": False, "context": lens.get("context_prompt", ""), "intent": oracle.get("predicted_intent"), "memory_count": memories.get("count", 0), "understanding": genesis.get("understanding_level", "surface"), "results": results}
