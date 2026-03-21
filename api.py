from fastapi import APIRouter, Header, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from auth import validate_api_key, signup_user, login_user, change_password
from rate_limiter import check_rate_limit, get_usage_stats, get_reset_time
from database import (
    get_db, user_update_key, admin_get_global_stats, user_get_all,
    usage_log, usage_by_layer, usage_count_total,
    notification_get_all, notification_mark_read, notification_count_unread,
    notification_save, webhook_save, webhook_get_all, webhook_delete,
    evolve_log, evolve_get_performance
)
from security import generate_api_key
from email_service import send_welcome, send_key_regenerated
from validators import validate_key_number

from pillar_nexus import (
    nexus_remember, nexus_recall, nexus_recall_global, nexus_forget, nexus_forget_user,
    nexus_get_all_memories, nexus_get_memory_stats, nexus_bulk_remember, nexus_search_by_tag,
    flux_check_cache, flux_store_cache, flux_invalidate, flux_get_stats, flux_warm_cache,
    pulse_health_check, pulse_report_incident, pulse_resolve_incident, pulse_get_health_report,
     pulse_auto_recover,
    insight_track, insight_get_stats, insight_get_growth,
    echo_cross_check, echo_verify_factual, echo_analyze_quality
)

from pillar_aegis import (
    vault_scan, vault_scan_batch, vault_scan_url, vault_get_security_report,
    sentinel_check_response, sentinel_check_batch,
    sovereign_check_compliance, sovereign_get_compliance_rate,
    abyss_detect_blind_spots, abyss_probe_unknown,
    infinite_process_paradox, infinite_hold_contradiction,
    conscience_check_ethics
)

from pillar_prometheus import (
    oracle_predict_intent, oracle_get_history, oracle_analyze_pattern,
    lens_analyze, lens_build_context_prompt,
    prima_process,
    deep_process_meaning, deep_get_sub_symbolic_definition,
    genesis_process, genesis_understand, genesis_generate_response, genesis_analyze_conversation_depth
)

from pillar_atlas import (
    atlas_detect_language, atlas_translate, atlas_translate_batch, atlas_auto_translate, atlas_get_languages,
    genome_build_profile, genome_get_profile, genome_inject_personality, genome_generate_system_prompt,
    nexus_connect_source, nexus_fetch_url, nexus_add_knowledge, nexus_get_knowledge, nexus_fuse_knowledge, nexus_get_sources,
    babel_translate_domain, babel_get_domains, babel_apply_lens,
    eternal_analyze_impact, eternal_get_patterns, eternal_compare_historical
)

from pillar_singularity import (
    duality_superpose, duality_evaluate_paradox,
    akasha_recognize_pattern, akasha_cross_domain_transfer,
    zero_analyze_absence, zero_detect_gaps, zero_find_data_gaps,
    apex_cultivate_emergence, apex_amplify_thinking,
    fractal_analyze_at_scale, fractal_multi_scale_analysis,
    origin_generate_first_principle, origin_probe_knowledge_gap, origin_map_frontier
)

from systems_network import (
    protocol_register_ai, protocol_send_message, protocol_get_messages, protocol_get_registered_ais, protocol_handoff,
    identity_create, identity_record_interaction, identity_get_reputation,
    transparency_log_decision, transparency_get_audit_trail, transparency_get_decision, transparency_generate_compliance_report,
    live_learning_submit_correction, live_learning_get_corrections, live_learning_apply_corrections,
    relationship_build, relationship_get, relationship_get_context_prompt,
    value_track, value_get_report, value_get_layer_roi
)

from systems_platform import (
    studio_create_workflow, studio_run_workflow, studio_get_workflows, studio_delete_workflow,
    neural_bus_publish, neural_bus_subscribe, neural_bus_consume,
    observatory_track_metric, observatory_get_dashboard, observatory_detect_anomaly,
    forge_create_experiment, forge_record_result, forge_get_results,
    time_machine_snapshot, time_machine_restore, time_machine_get_history,
    marketplace_publish, marketplace_search, marketplace_get_item,
    simulate_run, simulate_generate_profiles
)

from systems_god import (
    anima_initialize, anima_interact, anima_get_soul,
    akashic_extract_wisdom, akashic_query_wisdom, akashic_get_wisdom_summary,
    omega_analyze_trajectory, omega_get_prediction,
    truthfield_verify, truthfield_calibrate_confidence,
    empathon_read_emotional_reality, empathon_generate_presence
)

router = APIRouter()


def require_key(x_api_key: str = Header(...)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    user = validate_api_key(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    rate = check_rate_limit(x_api_key)
    if not rate["allowed"]:
        raise HTTPException(status_code=429, detail="Daily limit reached. Resets midnight UTC.")
    return user, x_api_key, get_db()


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

class TextBody(BaseModel):
    text: str

class MessageBody(BaseModel):
    message: str

class ResponseBody(BaseModel):
    response: str

class BatchResponseBody(BaseModel):
    responses: List[str]

class BatchMessageBody(BaseModel):
    messages: List[str]

class CacheCheckBody(BaseModel):
    question: str

class CacheStoreBody(BaseModel):
    question: str
    response: str

class WarmCacheBody(BaseModel):
    items: List[dict]

class IncidentBody(BaseModel):
    description: str
    severity: Optional[str] = "medium"

class InsightTrackBody(BaseModel):
    question: str
    response: str
    user_id: str
    response_time: Optional[float] = 0.0

class EchoCheckBody(BaseModel):
    response: str
    previous_responses: Optional[List[str]] = None

class EchoVerifyBody(BaseModel):
    statement: str
    context: str

class ScanUrlBody(BaseModel):
    url: str

class ComplianceBody(BaseModel):
    decision: str
    jurisdiction: str

class AbyssBody(BaseModel):
    text: str
    domain: str

class ProbeUnknownBody(BaseModel):
    question: str
    known_answers: Optional[List[str]] = None

class ParadoxBody(BaseModel):
    statement: str

class ContradictionBody(BaseModel):
    position_a: str
    position_b: str
    context: Optional[str] = ""

class OracleBody(BaseModel):
    message: str
    user_id: str

class LensBody(BaseModel):
    message: str
    user_id: str
    history: Optional[List[str]] = None

class TranslateBody(BaseModel):
    text: str
    target_language: str

class BatchTranslateBody(BaseModel):
    texts: List[str]
    target_language: str

class DetectLanguageBody(BaseModel):
    text: str

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

class BabelBody(BaseModel):
    concept: str
    source_domain: str
    target_domain: str

class BabelLensBody(BaseModel):
    problem: str
    domain: str

class EternalBody(BaseModel):
    decision: str
    domain: str
    time_horizon_years: Optional[int] = 100

class SuperposeBody(BaseModel):
    question: str
    possible_answers: List[str]
    context: Optional[str] = ""

class DualityParadoxBody(BaseModel):
    statement_a: str
    statement_b: str

class AkashaBody(BaseModel):
    text: str
    domain: str

class CrossDomainBody(BaseModel):
    pattern: str
    source_domain: str
    target_domain: str

class ZeroAbsenceBody(BaseModel):
    text: str
    context_type: str

class ZeroGapsBody(BaseModel):
    conversation: List[str]

class ZeroDataBody(BaseModel):
    dataset: List[dict]
    expected_fields: List[str]

class ApexBody(BaseModel):
    problem: str
    iterations: Optional[int] = 3

class FractalBody(BaseModel):
    problem: str
    scale: str

class MultiScaleBody(BaseModel):
    problem: str
    scales: List[str]

class OriginBody(BaseModel):
    domain: str

class KnowledgeGapBody(BaseModel):
    domain: str
    question: str

class FrontierBody(BaseModel):
    domains: List[str]

class GenesisUnderstandBody(BaseModel):
    text: str
    context: Optional[str] = ""

class EvolveTrackBody(BaseModel):
    question: str
    response: str
    score: int

class ProtocolRegisterBody(BaseModel):
    ai_id: str
    ai_name: str
    ai_type: str
    capabilities: Optional[List[str]] = None
    version: Optional[str] = "1.0"

class ProtocolMessageBody(BaseModel):
    from_ai: str
    to_ai: str
    message: str
    message_type: Optional[str] = "request"
    priority: Optional[str] = "normal"

class ProtocolHandoffBody(BaseModel):
    from_ai: str
    to_ai: str
    context: dict

class IdentityRecordBody(BaseModel):
    ai_id: str
    was_accurate: Optional[bool] = True
    user_rating: Optional[float] = None

class TransparencyLogBody(BaseModel):
    ai_id: str
    decision: str
    reasoning: str
    outcome: Optional[str] = ""
    affected_users: Optional[int] = 0

class CorrectionBody(BaseModel):
    ai_id: str
    original_response: str
    corrected_response: str
    correction_type: str
    context: Optional[str] = ""

class ApplyCorrectionBody(BaseModel):
    ai_id: str
    response: str

class RelationshipBody(BaseModel):
    user_id: str
    ai_id: str
    interaction_content: Optional[str] = ""
    interaction_quality: Optional[int] = 5

class ValueTrackBody(BaseModel):
    user_id: Optional[str] = ""
    interaction_type: Optional[str] = ""
    goal_achieved: Optional[bool] = False
    time_saved_minutes: Optional[int] = 0
    estimated_value_usd: Optional[float] = 0.0
    layer_used: Optional[str] = ""

class WorkflowBody(BaseModel):
    name: str
    description: Optional[str] = ""
    steps: List[dict]
    trigger: Optional[str] = "manual"

class WorkflowRunBody(BaseModel):
    workflow_id: str
    input_data: dict

class NeuralBusPublishBody(BaseModel):
    topic: str
    payload: dict
    publisher_id: Optional[str] = ""
    priority: Optional[str] = "normal"

class NeuralBusSubscribeBody(BaseModel):
    topic: str
    subscriber_id: str

class NeuralBusConsumeBody(BaseModel):
    topic: str
    subscriber_id: str
    limit: Optional[int] = 10

class ObservatoryMetricBody(BaseModel):
    metric_name: str
    value: float
    ai_id: Optional[str] = ""
    dimension: Optional[str] = "performance"
    unit: Optional[str] = ""

class AnomalyBody(BaseModel):
    metric_name: str
    current_value: float

class ForgeExperimentBody(BaseModel):
    name: str
    hypothesis: str
    variant_a: str
    variant_b: str
    metric_to_track: Optional[str] = "quality_score"

class ForgeResultBody(BaseModel):
    experiment_id: str
    variant: str
    score: float

class TimeMachineSnapshotBody(BaseModel):
    ai_id: str
    state_data: dict
    label: Optional[str] = ""

class MarketplacePublishBody(BaseModel):
    item_name: str
    item_type: str
    description: str
    config_data: dict
    price_usd: Optional[float] = 0.0
    tags: Optional[List[str]] = None

class SimulateBody(BaseModel):
    scenario_name: str
    ai_config: dict
    user_profiles: List[dict]
    iterations: Optional[int] = 10

class SimulateProfilesBody(BaseModel):
    count: int
    profile_types: List[str]

class AnimaInitBody(BaseModel):
    ai_id: str
    core_values: Optional[List[str]] = None
    identity_description: Optional[str] = ""

class AnimaInteractBody(BaseModel):
    ai_id: str
    interaction_content: str
    interaction_quality: Optional[int] = 5
    user_id: Optional[str] = ""

class AkashicExtractBody(BaseModel):
    interaction_content: str
    correction_content: str
    interaction_type: str

class OmegaTrajectoryBody(BaseModel):
    user_id: str
    recent_messages: Optional[List[str]] = None

class TruthfieldBody(BaseModel):
    response: str
    context: Optional[str] = ""

class TruthfieldCalibrateBody(BaseModel):
    statement: str
    actual_confidence: float

class EmpathonReadBody(BaseModel):
    message: str
    conversation_history: Optional[List[str]] = None

class EmpathonPresenceBody(BaseModel):
    message: str
    emotional_reading: dict

class WebhookBody(BaseModel):
    url: str
    events: List[str]

class NotificationReadBody(BaseModel):
    notification_id: str

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
    return {"status": "created", "email": body.email, "api_key_1": result["api_key_1"], "api_key_2": result["api_key_2"], "access_token": result["access_token"], "token_type": "bearer", "message": "Welcome to KRONYX. 2 API keys created.", "disclaimer": "You are responsible for all usage under your API keys."}


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
    user, api_key, db = auth
    valid, err = validate_key_number(key_number)
    if not valid:
        raise HTTPException(status_code=400, detail=err)
    new_key = generate_api_key()
    success = user_update_key(user["id"], key_number, new_key)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to regenerate key")
    send_key_regenerated(user["email"], new_key, key_number)
    return {"status": "regenerated", "key_number": key_number, "new_key": new_key, "warning": "Old key permanently deactivated. Update your code immediately."}


@router.post("/v1/account/change-password")
async def change_pwd(body: ChangePasswordBody, auth=Depends(require_key)):
    user, api_key, db = auth
    result = change_password(user["id"], body.old_password, body.new_password, user["password"])
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/v1/account/dashboard")
async def dashboard(auth=Depends(require_key)):
    user, api_key, db = auth
    return {"email": user["email"], "api_key_1": user["api_key_1"], "api_key_2": user["api_key_2"], "memory_stats": nexus_get_memory_stats(api_key, db), "cache_stats": flux_get_stats(api_key, db), "health": pulse_health_check(db), "usage": get_usage_stats(api_key), "insight": insight_get_stats(api_key, db), "more_keys": "coming_soon", "team_members": "coming_soon", "pro_plan": "coming_soon"}


@router.get("/v1/account/usage")
async def usage(auth=Depends(require_key)):
    user, api_key, db = auth
    stats = get_usage_stats(api_key)
    stats["reset_info"] = get_reset_time()
    stats["by_layer"] = usage_by_layer(api_key)
    return stats


@router.post("/v1/nexus-core/memex/remember")
async def api_remember(body: RememberBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_remember(body.content, body.user_id, key, db, body.tags)


@router.post("/v1/nexus-core/memex/recall")
async def api_recall(body: RecallBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_recall(body.query, body.user_id, key, db, body.limit or 5)


@router.post("/v1/nexus-core/memex/recall-global")
async def api_recall_global(body: CacheCheckBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_recall_global(body.question, key, db)


@router.delete("/v1/nexus-core/memex/forget/{memory_id}")
async def api_forget(memory_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_forget(memory_id, key, db)


@router.post("/v1/nexus-core/memex/forget-user")
async def api_forget_user(body: ForgetUserBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_forget_user(body.user_id, key, db)


@router.get("/v1/nexus-core/memex/all")
async def api_all_memories(user_id: Optional[str] = None, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_get_all_memories(key, db, user_id)


@router.get("/v1/nexus-core/memex/stats")
async def api_memory_stats(auth=Depends(require_key)):
    user, key, db = auth
    return nexus_get_memory_stats(key, db)


@router.post("/v1/nexus-core/memex/bulk")
async def api_bulk_remember(body: BulkRememberBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_bulk_remember(body.items, key, db)


@router.post("/v1/nexus-core/memex/tag-search")
async def api_tag_search(body: TagSearchBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_search_by_tag(body.tag, key, db, body.user_id, body.limit or 10)


@router.post("/v1/nexus-core/flux/check")
async def api_flux_check(body: CacheCheckBody, auth=Depends(require_key)):
    user, key, db = auth
    return flux_check_cache(body.question, key, db)


@router.post("/v1/nexus-core/flux/store")
async def api_flux_store(body: CacheStoreBody, auth=Depends(require_key)):
    user, key, db = auth
    return flux_store_cache(body.question, body.response, key, db)


@router.post("/v1/nexus-core/flux/invalidate")
async def api_flux_invalidate(body: CacheCheckBody, auth=Depends(require_key)):
    user, key, db = auth
    return flux_invalidate(body.question, key, db)


@router.get("/v1/nexus-core/flux/stats")
async def api_flux_stats(auth=Depends(require_key)):
    user, key, db = auth
    return flux_get_stats(key, db)


@router.post("/v1/nexus-core/flux/warm")
async def api_flux_warm(body: WarmCacheBody, auth=Depends(require_key)):
    user, key, db = auth
    return flux_warm_cache(body.items, key, db)


@router.get("/v1/nexus-core/pulse/health")
async def api_pulse_health():
    return pulse_health_check(get_db())


@router.post("/v1/nexus-core/pulse/incident")
async def api_pulse_incident(body: IncidentBody, auth=Depends(require_key)):
    user, key, db = auth
    return pulse_report_incident(key, body.description, db, body.severity or "medium")


@router.post("/v1/nexus-core/pulse/resolve/{incident_id}")
async def api_pulse_resolve(incident_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return pulse_resolve_incident(incident_id, key, db)


@router.get("/v1/nexus-core/pulse/report")
async def api_pulse_report(auth=Depends(require_key)):
    user, key, db = auth
    return pulse_get_health_report(key, db)


@router.post("/v1/nexus-core/pulse/auto-recover")
async def api_pulse_recover(auth=Depends(require_key)):
    user, key, db = auth
    return pulse_auto_recover(key, db)


@router.post("/v1/nexus-core/insight/track")
async def api_insight_track(body: InsightTrackBody, auth=Depends(require_key)):
    user, key, db = auth
    return insight_track(body.question, body.response, body.user_id, key, db, body.response_time or 0.0)


@router.get("/v1/nexus-core/insight/stats")
async def api_insight_stats(auth=Depends(require_key)):
    user, key, db = auth
    return insight_get_stats(key, db)


@router.get("/v1/nexus-core/insight/growth")
async def api_insight_growth(auth=Depends(require_key)):
    user, key, db = auth
    return insight_get_growth(key, db)


@router.post("/v1/nexus-core/echo/check")
async def api_echo_check(body: EchoCheckBody, auth=Depends(require_key)):
    user, key, db = auth
    return echo_cross_check(body.response, body.previous_responses or [], key, db)


@router.post("/v1/nexus-core/echo/verify")
async def api_echo_verify(body: EchoVerifyBody, auth=Depends(require_key)):
    user, key, db = auth
    return echo_verify_factual(body.statement, body.context, key, db)


@router.post("/v1/nexus-core/echo/quality")
async def api_echo_quality(body: ResponseBody, auth=Depends(require_key)):
    user, key, db = auth
    return echo_analyze_quality(body.response, key, db)


@router.post("/v1/aegis-shield/vault/scan")
async def api_vault_scan(body: MessageBody, auth=Depends(require_key)):
    user, key, db = auth
    return vault_scan(body.message, key, db)


@router.post("/v1/aegis-shield/vault/scan-batch")
async def api_vault_batch(body: BatchMessageBody, auth=Depends(require_key)):
    user, key, db = auth
    return vault_scan_batch(body.messages, key, db)


@router.post("/v1/aegis-shield/vault/scan-url")
async def api_vault_url(body: ScanUrlBody, auth=Depends(require_key)):
    user, key, db = auth
    return vault_scan_url(body.url, key, db)


@router.get("/v1/aegis-shield/vault/report")
async def api_vault_report(auth=Depends(require_key)):
    user, key, db = auth
    return vault_get_security_report(key, db)


@router.post("/v1/aegis-shield/sentinel/check")
async def api_sentinel_check(body: ResponseBody, auth=Depends(require_key)):
    user, key, db = auth
    return sentinel_check_response(body.response, key, db)


@router.post("/v1/aegis-shield/sentinel/check-batch")
async def api_sentinel_batch(body: BatchResponseBody, auth=Depends(require_key)):
    user, key, db = auth
    return sentinel_check_batch(body.responses, key, db)


@router.post("/v1/aegis-shield/sovereign/check")
async def api_sovereign_check(body: ComplianceBody, auth=Depends(require_key)):
    user, key, db = auth
    return sovereign_check_compliance(body.decision, body.jurisdiction, key, db)


@router.get("/v1/aegis-shield/sovereign/rate")
async def api_sovereign_rate(auth=Depends(require_key)):
    user, key, db = auth
    return sovereign_get_compliance_rate(key, db)


@router.post("/v1/aegis-shield/abyss/blindspots")
async def api_abyss_blindspots(body: AbyssBody, auth=Depends(require_key)):
    user, key, db = auth
    return abyss_detect_blind_spots(body.text, body.domain, key, db)


@router.post("/v1/aegis-shield/abyss/probe")
async def api_abyss_probe(body: ProbeUnknownBody, auth=Depends(require_key)):
    user, key, db = auth
    return abyss_probe_unknown(body.question, body.known_answers or [], key, db)


@router.post("/v1/aegis-shield/infinite/paradox")
async def api_infinite_paradox(body: ParadoxBody, auth=Depends(require_key)):
    user, key, db = auth
    return infinite_process_paradox(body.statement, key, db)


@router.post("/v1/aegis-shield/infinite/hold")
async def api_infinite_hold(body: ContradictionBody, auth=Depends(require_key)):
    user, key, db = auth
    return infinite_hold_contradiction(body.position_a, body.position_b, body.context or "", key, db)


@router.post("/v1/aegis-shield/conscience/check")
async def api_conscience_check(body: TextBody, auth=Depends(require_key)):
    user, key, db = auth
    return conscience_check_ethics(body.text, key, db)


@router.post("/v1/prometheus-mind/oracle/predict")
async def api_oracle_predict(body: OracleBody, auth=Depends(require_key)):
    user, key, db = auth
    return oracle_predict_intent(body.message, body.user_id, key, db)


@router.get("/v1/prometheus-mind/oracle/history/{user_id}")
async def api_oracle_history(user_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return oracle_get_history(key, user_id, db)


@router.post("/v1/prometheus-mind/oracle/analyze")
async def api_oracle_analyze(body: BatchMessageBody, auth=Depends(require_key)):
    user, key, db = auth
    return oracle_analyze_pattern(body.messages, key, db)


@router.post("/v1/prometheus-mind/lens/analyze")
async def api_lens_analyze(body: LensBody, auth=Depends(require_key)):
    user, key, db = auth
    return lens_analyze(body.message, body.user_id, key, db, body.history)


@router.post("/v1/prometheus-mind/lens/context")
async def api_lens_context(body: LensBody, auth=Depends(require_key)):
    user, key, db = auth
    return lens_build_context_prompt(body.message, body.user_id, key, db)


@router.post("/v1/prometheus-mind/prima/process")
async def api_prima_process(body: TextBody, auth=Depends(require_key)):
    user, key, db = auth
    return prima_process(body.text, key, db)


@router.post("/v1/prometheus-mind/deep/meaning")
async def api_deep_meaning(body: TextBody, auth=Depends(require_key)):
    user, key, db = auth
    return deep_process_meaning(body.text, key, db)


@router.get("/v1/prometheus-mind/deep/define/{concept}")
async def api_deep_define(concept: str, auth=Depends(require_key)):
    user, key, db = auth
    return deep_get_sub_symbolic_definition(concept, key, db)


@router.post("/v1/prometheus-mind/genesis/process")
async def api_genesis_process(body: TextBody, auth=Depends(require_key)):
    user, key, db = auth
    return genesis_process(body.text, key, db)


@router.post("/v1/prometheus-mind/genesis/understand")
async def api_genesis_understand(body: GenesisUnderstandBody, auth=Depends(require_key)):
    user, key, db = auth
    return genesis_understand(body.text, body.context or "", key, db)


@router.post("/v1/prometheus-mind/genesis/respond")
async def api_genesis_respond(body: TextBody, auth=Depends(require_key)):
    user, key, db = auth
    return genesis_generate_response(body.text, key, db)


@router.post("/v1/prometheus-mind/genesis/conversation-depth")
async def api_genesis_depth(body: BatchMessageBody, auth=Depends(require_key)):
    user, key, db = auth
    return genesis_analyze_conversation_depth(body.messages, key, db)


@router.post("/v1/atlas-prime/atlas/translate")
async def api_atlas_translate(body: TranslateBody, auth=Depends(require_key)):
    user, key, db = auth
    return atlas_translate(body.text, body.target_language, key, db)


@router.post("/v1/atlas-prime/atlas/translate-batch")
async def api_atlas_batch(body: BatchTranslateBody, auth=Depends(require_key)):
    user, key, db = auth
    return atlas_translate_batch(body.texts, body.target_language, key, db)


@router.post("/v1/atlas-prime/atlas/detect")
async def api_atlas_detect(body: DetectLanguageBody, auth=Depends(require_key)):
    user, key, db = auth
    return atlas_detect_language(body.text)


@router.post("/v1/atlas-prime/atlas/auto")
async def api_atlas_auto(body: TranslateBody, auth=Depends(require_key)):
    user, key, db = auth
    return atlas_auto_translate(body.text, body.target_language, key, db)


@router.get("/v1/atlas-prime/atlas/languages")
async def api_atlas_languages():
    return atlas_get_languages()


@router.post("/v1/atlas-prime/genome/build")
async def api_genome_build(body: GenomeProfileBody, auth=Depends(require_key)):
    user, key, db = auth
    return genome_build_profile(body.business_name, body.business_type, body.tone or "professional", body.vocabulary or "general", body.personality_traits or [], body.preferred_words or [], body.avoid_words or [], key, db)


@router.get("/v1/atlas-prime/genome/profile")
async def api_genome_profile(auth=Depends(require_key)):
    user, key, db = auth
    return genome_get_profile(key, db)


@router.post("/v1/atlas-prime/genome/inject")
async def api_genome_inject(body: InjectBody, auth=Depends(require_key)):
    user, key, db = auth
    return genome_inject_personality(body.response, key, db)


@router.get("/v1/atlas-prime/genome/prompt")
async def api_genome_prompt(auth=Depends(require_key)):
    user, key, db = auth
    return genome_generate_system_prompt(key, db)


@router.post("/v1/atlas-prime/nexus/connect")
async def api_nexus_connect(body: NexusSourceBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_connect_source(body.source_type, body.source_url, key, db, body.name or "", body.refresh_minutes or 60)


@router.post("/v1/atlas-prime/nexus/fetch")
async def api_nexus_fetch(body: CacheCheckBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_fetch_url(body.question, key, db)


@router.post("/v1/atlas-prime/nexus/knowledge")
async def api_nexus_add(body: NexusKnowledgeBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_add_knowledge(body.content, body.topic, key, db)


@router.get("/v1/atlas-prime/nexus/knowledge/{topic}")
async def api_nexus_get(topic: str, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_get_knowledge(topic, key, db)


@router.post("/v1/atlas-prime/nexus/fuse")
async def api_nexus_fuse(body: CacheCheckBody, auth=Depends(require_key)):
    user, key, db = auth
    return nexus_fuse_knowledge(body.question, key, db)


@router.get("/v1/atlas-prime/nexus/sources")
async def api_nexus_sources(auth=Depends(require_key)):
    user, key, db = auth
    return nexus_get_sources(key, db)


@router.post("/v1/atlas-prime/babel/translate")
async def api_babel_translate(body: BabelBody, auth=Depends(require_key)):
    user, key, db = auth
    return babel_translate_domain(body.concept, body.source_domain, body.target_domain, key, db)


@router.get("/v1/atlas-prime/babel/domains")
async def api_babel_domains(auth=Depends(require_key)):
    user, key, db = auth
    return babel_get_domains()


@router.post("/v1/atlas-prime/babel/lens")
async def api_babel_lens(body: BabelLensBody, auth=Depends(require_key)):
    user, key, db = auth
    return babel_apply_lens(body.problem, body.domain, key, db)


@router.post("/v1/atlas-prime/eternal/impact")
async def api_eternal_impact(body: EternalBody, auth=Depends(require_key)):
    user, key, db = auth
    return eternal_analyze_impact(body.decision, body.domain, key, db, body.time_horizon_years or 100)


@router.get("/v1/atlas-prime/eternal/patterns")
async def api_eternal_patterns(auth=Depends(require_key)):
    user, key, db = auth
    return eternal_get_patterns()


@router.post("/v1/singularity/duality/superpose")
async def api_duality_superpose(body: SuperposeBody, auth=Depends(require_key)):
    user, key, db = auth
    return duality_superpose(body.question, body.possible_answers, body.context or "", key, db)


@router.post("/v1/singularity/duality/paradox")
async def api_duality_paradox(body: DualityParadoxBody, auth=Depends(require_key)):
    user, key, db = auth
    return duality_evaluate_paradox(body.statement_a, body.statement_b, key, db)


@router.post("/v1/singularity/akasha/recognize")
async def api_akasha_recognize(body: AkashaBody, auth=Depends(require_key)):
    user, key, db = auth
    return akasha_recognize_pattern(body.text, body.domain, key, db)


@router.post("/v1/singularity/akasha/transfer")
async def api_akasha_transfer(body: CrossDomainBody, auth=Depends(require_key)):
    user, key, db = auth
    return akasha_cross_domain_transfer(body.pattern, body.source_domain, body.target_domain, key, db)


@router.post("/v1/singularity/zero/absence")
async def api_zero_absence(body: ZeroAbsenceBody, auth=Depends(require_key)):
    user, key, db = auth
    return zero_analyze_absence(body.text, body.context_type, key, db)


@router.post("/v1/singularity/zero/gaps")
async def api_zero_gaps(body: ZeroGapsBody, auth=Depends(require_key)):
    user, key, db = auth
    return zero_detect_gaps(body.conversation, key, db)


@router.post("/v1/singularity/zero/data-gaps")
async def api_zero_data(body: ZeroDataBody, auth=Depends(require_key)):
    user, key, db = auth
    return zero_find_data_gaps(body.dataset, body.expected_fields, key, db)


@router.post("/v1/singularity/apex/cultivate")
async def api_apex_cultivate(body: ApexBody, auth=Depends(require_key)):
    user, key, db = auth
    return apex_cultivate_emergence(body.problem, key, db, body.iterations or 3)


@router.post("/v1/singularity/apex/amplify")
async def api_apex_amplify(body: TextBody, auth=Depends(require_key)):
    user, key, db = auth
    return apex_amplify_thinking(body.text, key, db)


@router.post("/v1/singularity/fractal/scale")
async def api_fractal_scale(body: FractalBody, auth=Depends(require_key)):
    user, key, db = auth
    return fractal_analyze_at_scale(body.problem, body.scale, key, db)


@router.post("/v1/singularity/fractal/multi-scale")
async def api_fractal_multi(body: MultiScaleBody, auth=Depends(require_key)):
    user, key, db = auth
    return fractal_multi_scale_analysis(body.problem, body.scales, key, db)


@router.post("/v1/singularity/origin/generate")
async def api_origin_generate(body: OriginBody, auth=Depends(require_key)):
    user, key, db = auth
    return origin_generate_first_principle(body.domain, key, db)


@router.post("/v1/singularity/origin/probe")
async def api_origin_probe(body: KnowledgeGapBody, auth=Depends(require_key)):
    user, key, db = auth
    return origin_probe_knowledge_gap(body.domain, body.question, key, db)


@router.post("/v1/singularity/origin/frontier")
async def api_origin_frontier(body: FrontierBody, auth=Depends(require_key)):
    user, key, db = auth
    return origin_map_frontier(body.domains, key, db)


@router.post("/v1/systems/protocol/register")
async def api_protocol_register(body: ProtocolRegisterBody, auth=Depends(require_key)):
    user, key, db = auth
    return protocol_register_ai(body.ai_id, body.ai_name, body.ai_type, key, db, body.capabilities, body.version or "1.0")


@router.post("/v1/systems/protocol/send")
async def api_protocol_send(body: ProtocolMessageBody, auth=Depends(require_key)):
    user, key, db = auth
    return protocol_send_message(body.from_ai, body.to_ai, body.message, key, db, body.message_type or "request", body.priority or "normal")


@router.get("/v1/systems/protocol/messages/{ai_id}")
async def api_protocol_get(ai_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return protocol_get_messages(ai_id, key, db)


@router.get("/v1/systems/protocol/registered")
async def api_protocol_list(auth=Depends(require_key)):
    user, key, db = auth
    return protocol_get_registered_ais(key, db)


@router.post("/v1/systems/protocol/handoff")
async def api_protocol_handoff(body: ProtocolHandoffBody, auth=Depends(require_key)):
    user, key, db = auth
    return protocol_handoff(body.from_ai, body.to_ai, body.context, key, db)


@router.post("/v1/systems/identity/create")
async def api_identity_create(body: AnimaInitBody, auth=Depends(require_key)):
    user, key, db = auth
    return identity_create(body.ai_id, key, db)


@router.post("/v1/systems/identity/record")
async def api_identity_record(body: IdentityRecordBody, auth=Depends(require_key)):
    user, key, db = auth
    return identity_record_interaction(body.ai_id, key, db, body.was_accurate if body.was_accurate is not None else True, body.user_rating)


@router.get("/v1/systems/identity/reputation/{ai_id}")
async def api_identity_reputation(ai_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return identity_get_reputation(ai_id, key, db)


@router.post("/v1/systems/transparency/log")
async def api_transparency_log(body: TransparencyLogBody, auth=Depends(require_key)):
    user, key, db = auth
    return transparency_log_decision(body.ai_id, body.decision, body.reasoning, key, db, body.outcome or "", body.affected_users or 0)


@router.get("/v1/systems/transparency/audit/{ai_id}")
async def api_transparency_audit(ai_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return transparency_get_audit_trail(ai_id, key, db)


@router.post("/v1/systems/transparency/compliance-report")
async def api_transparency_compliance(body: ComplianceBody, auth=Depends(require_key)):
    user, key, db = auth
    return transparency_generate_compliance_report(key, db, body.jurisdiction)


@router.post("/v1/systems/live-learning/correction")
async def api_live_learning_correction(body: CorrectionBody, auth=Depends(require_key)):
    user, key, db = auth
    return live_learning_submit_correction(body.ai_id, body.original_response, body.corrected_response, body.correction_type, key, db, body.context or "")


@router.get("/v1/systems/live-learning/corrections")
async def api_live_learning_get(auth=Depends(require_key)):
    user, key, db = auth
    return live_learning_get_corrections(key, db)


@router.post("/v1/systems/live-learning/apply")
async def api_live_learning_apply(body: ApplyCorrectionBody, auth=Depends(require_key)):
    user, key, db = auth
    return live_learning_apply_corrections(body.ai_id, body.response, key, db)


@router.post("/v1/systems/relationship/build")
async def api_relationship_build(body: RelationshipBody, auth=Depends(require_key)):
    user, key, db = auth
    return relationship_build(body.user_id, body.ai_id, key, db, body.interaction_content or "", body.interaction_quality or 5)


@router.post("/v1/systems/relationship/get")
async def api_relationship_get(body: RelationshipBody, auth=Depends(require_key)):
    user, key, db = auth
    return relationship_get(body.user_id, body.ai_id, key, db)


@router.post("/v1/systems/relationship/context-prompt")
async def api_relationship_context(body: RelationshipBody, auth=Depends(require_key)):
    user, key, db = auth
    return relationship_get_context_prompt(body.user_id, body.ai_id, key, db)


@router.post("/v1/systems/value/track")
async def api_value_track(body: ValueTrackBody, auth=Depends(require_key)):
    user, key, db = auth
    return value_track(key, db, body.user_id or "", body.interaction_type or "", body.goal_achieved or False, body.time_saved_minutes or 0, body.estimated_value_usd or 0.0, body.layer_used or "")


@router.get("/v1/systems/value/report")
async def api_value_report(auth=Depends(require_key)):
    user, key, db = auth
    return value_get_report(key, db)


@router.get("/v1/systems/value/roi")
async def api_value_roi(auth=Depends(require_key)):
    user, key, db = auth
    return value_get_layer_roi(key, db)


@router.post("/v1/systems/studio/workflow")
async def api_studio_create(body: WorkflowBody, auth=Depends(require_key)):
    user, key, db = auth
    return studio_create_workflow(body.name, body.description or "", body.steps, key, db, body.trigger or "manual")


@router.post("/v1/systems/studio/run")
async def api_studio_run(body: WorkflowRunBody, auth=Depends(require_key)):
    user, key, db = auth
    return studio_run_workflow(body.workflow_id, body.input_data, key, db)


@router.get("/v1/systems/studio/workflows")
async def api_studio_list(auth=Depends(require_key)):
    user, key, db = auth
    return studio_get_workflows(key, db)


@router.post("/v1/systems/neural-bus/publish")
async def api_neural_publish(body: NeuralBusPublishBody, auth=Depends(require_key)):
    user, key, db = auth
    return neural_bus_publish(body.topic, body.payload, key, db, body.publisher_id or "", body.priority or "normal")


@router.post("/v1/systems/neural-bus/subscribe")
async def api_neural_subscribe(body: NeuralBusSubscribeBody, auth=Depends(require_key)):
    user, key, db = auth
    return neural_bus_subscribe(body.topic, body.subscriber_id, key, db)


@router.post("/v1/systems/neural-bus/consume")
async def api_neural_consume(body: NeuralBusConsumeBody, auth=Depends(require_key)):
    user, key, db = auth
    return neural_bus_consume(body.topic, body.subscriber_id, key, db, body.limit or 10)


@router.post("/v1/systems/observatory/track")
async def api_observatory_track(body: ObservatoryMetricBody, auth=Depends(require_key)):
    user, key, db = auth
    return observatory_track_metric(body.metric_name, body.value, key, db, body.ai_id or "", body.dimension or "performance", body.unit or "")


@router.get("/v1/systems/observatory/dashboard")
async def api_observatory_dashboard(ai_id: Optional[str] = None, auth=Depends(require_key)):
    user, key, db = auth
    return observatory_get_dashboard(key, db, ai_id)


@router.post("/v1/systems/observatory/anomaly")
async def api_observatory_anomaly(body: AnomalyBody, auth=Depends(require_key)):
    user, key, db = auth
    return observatory_detect_anomaly(body.metric_name, body.current_value, key, db)


@router.post("/v1/systems/forge/experiment")
async def api_forge_experiment(body: ForgeExperimentBody, auth=Depends(require_key)):
    user, key, db = auth
    return forge_create_experiment(body.name, body.hypothesis, body.variant_a, body.variant_b, key, db, body.metric_to_track or "quality_score")


@router.post("/v1/systems/forge/result")
async def api_forge_result(body: ForgeResultBody, auth=Depends(require_key)):
    user, key, db = auth
    return forge_record_result(body.experiment_id, body.variant, body.score, key, db)


@router.get("/v1/systems/forge/results/{experiment_id}")
async def api_forge_results(experiment_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return forge_get_results(experiment_id, key, db)


@router.post("/v1/systems/time-machine/snapshot")
async def api_time_snapshot(body: TimeMachineSnapshotBody, auth=Depends(require_key)):
    user, key, db = auth
    return time_machine_snapshot(body.ai_id, body.state_data, key, db, body.label or "")


@router.get("/v1/systems/time-machine/restore/{snapshot_id}")
async def api_time_restore(snapshot_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return time_machine_restore(snapshot_id, key, db)


@router.get("/v1/systems/time-machine/history/{ai_id}")
async def api_time_history(ai_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return time_machine_get_history(ai_id, key, db)


@router.post("/v1/systems/marketplace/publish")
async def api_marketplace_publish(body: MarketplacePublishBody, auth=Depends(require_key)):
    user, key, db = auth
    return marketplace_publish(body.item_name, body.item_type, body.description, body.config_data, key, db, body.price_usd or 0.0, body.tags)


@router.get("/v1/systems/marketplace/search")
async def api_marketplace_search(q: Optional[str] = None, item_type: Optional[str] = None, free_only: Optional[bool] = False, auth=Depends(require_key)):
    user, key, db = auth
    return marketplace_search(q or "", key, db, item_type, free_only or False)


@router.get("/v1/systems/marketplace/item/{item_id}")
async def api_marketplace_item(item_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return marketplace_get_item(item_id, key, db)


@router.post("/v1/systems/simulate/run")
async def api_simulate_run(body: SimulateBody, auth=Depends(require_key)):
    user, key, db = auth
    return simulate_run(body.scenario_name, body.ai_config, body.user_profiles, key, db, body.iterations or 10)


@router.post("/v1/systems/simulate/profiles")
async def api_simulate_profiles(body: SimulateProfilesBody, auth=Depends(require_key)):
    user, key, db = auth
    return simulate_generate_profiles(body.count, body.profile_types, key, db)


@router.post("/v1/god/anima/initialize")
async def api_anima_init(body: AnimaInitBody, auth=Depends(require_key)):
    user, key, db = auth
    return anima_initialize(body.ai_id, key, db, body.core_values, body.identity_description or "")


@router.post("/v1/god/anima/interact")
async def api_anima_interact(body: AnimaInteractBody, auth=Depends(require_key)):
    user, key, db = auth
    return anima_interact(body.ai_id, body.interaction_content, key, db, body.interaction_quality or 5, body.user_id or "")


@router.get("/v1/god/anima/soul/{ai_id}")
async def api_anima_soul(ai_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return anima_get_soul(ai_id, key, db)


@router.post("/v1/god/akashic/extract")
async def api_akashic_extract(body: AkashicExtractBody, auth=Depends(require_key)):
    user, key, db = auth
    return akashic_extract_wisdom(body.interaction_content, body.correction_content, body.interaction_type, key, db)


@router.post("/v1/god/akashic/query")
async def api_akashic_query(body: TextBody, auth=Depends(require_key)):
    user, key, db = auth
    return akashic_query_wisdom(body.text, key, db)


@router.get("/v1/god/akashic/summary")
async def api_akashic_summary(auth=Depends(require_key)):
    user, key, db = auth
    return akashic_get_wisdom_summary(key, db)


@router.post("/v1/god/omega/trajectory")
async def api_omega_trajectory(body: OmegaTrajectoryBody, auth=Depends(require_key)):
    user, key, db = auth
    return omega_analyze_trajectory(body.user_id, key, db, body.recent_messages)


@router.get("/v1/god/omega/prediction/{user_id}")
async def api_omega_prediction(user_id: str, auth=Depends(require_key)):
    user, key, db = auth
    return omega_get_prediction(user_id, key, db)


@router.post("/v1/god/truthfield/verify")
async def api_truthfield_verify(body: TruthfieldBody, auth=Depends(require_key)):
    user, key, db = auth
    return truthfield_verify(body.response, key, db, body.context or "")


@router.post("/v1/god/truthfield/calibrate")
async def api_truthfield_calibrate(body: TruthfieldCalibrateBody, auth=Depends(require_key)):
    user, key, db = auth
    return truthfield_calibrate_confidence(body.statement, body.actual_confidence, key, db)


@router.post("/v1/god/empathon/read")
async def api_empathon_read(body: EmpathonReadBody, auth=Depends(require_key)):
    user, key, db = auth
    return empathon_read_emotional_reality(body.message, key, db, body.conversation_history)


@router.post("/v1/god/empathon/presence")
async def api_empathon_presence(body: EmpathonPresenceBody, auth=Depends(require_key)):
    user, key, db = auth
    return empathon_generate_presence(body.message, body.emotional_reading, key, db)


@router.post("/v1/evolve/track")
async def api_evolve_track(body: EvolveTrackBody, auth=Depends(require_key)):
    user, key, db = auth
    if not (0 <= body.score <= 100):
        raise HTTPException(status_code=400, detail="score must be 0 to 100")
    evolve_log(key, body.question, body.response, body.score)
    usage_log(key, "evolve", "track")
    return {"status": "tracked", "score": body.score}


@router.get("/v1/evolve/performance")
async def api_evolve_performance(auth=Depends(require_key)):
    user, key, db = auth
    perf = evolve_get_performance(key)
    avg = perf.get("average_score", 0)
    grade = "A" if avg >= 90 else "B" if avg >= 80 else "C" if avg >= 70 else "D"
    return {"average_score": avg, "grade": grade, "total_tracked": perf.get("total_tracked", 0), "trend": perf.get("trend", "no_data")}


@router.get("/v1/notifications")
async def api_get_notifications(unread_only: Optional[bool] = False, auth=Depends(require_key)):
    user, key, db = auth
    return {"notifications": notification_get_all(key, unread_only or False), "unread_count": notification_count_unread(key)}


@router.post("/v1/notifications/read")
async def api_mark_read(body: NotificationReadBody, auth=Depends(require_key)):
    user, key, db = auth
    notification_mark_read(body.notification_id)
    return {"status": "read"}


@router.post("/v1/webhooks/register")
async def api_webhook_register(body: WebhookBody, auth=Depends(require_key)):
    user, key, db = auth
    success = webhook_save(key, body.url, body.events)
    return {"status": "registered" if success else "error"}


@router.get("/v1/webhooks")
async def api_webhook_list(auth=Depends(require_key)):
    user, key, db = auth
    return {"webhooks": webhook_get_all(key)}


@router.delete("/v1/webhooks/{webhook_id}")
async def api_webhook_delete(webhook_id: str, auth=Depends(require_key)):
    user, key, db = auth
    webhook_delete(webhook_id, key)
    return {"status": "deleted"}


@router.get("/v1/admin/stats", include_in_schema=False)
async def api_admin_stats(x_admin_key: str = Header(...)):
    import os
    if not x_admin_key or x_admin_key != os.getenv("ADMIN_KEY", ""):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    stats = admin_get_global_stats()
    stats["total_registered_users"] = len(user_get_all())
    return stats


@router.post("/v1/flow/complete")
async def api_complete_flow(body: CompleteFlowBody, auth=Depends(require_key)):
    user, key, db = auth
    results = {}
    vault_result = vault_scan(body.message, key, db)
    results["vault"] = vault_result
    if not vault_result.get("is_safe"):
        return {"blocked": True, "reason": vault_result.get("threat"), "results": results}
    cached = flux_check_cache(body.message, key, db)
    results["flux"] = cached
    if cached.get("hit"):
        return {"blocked": False, "cache_hit": True, "response": cached.get("response"), "results": results}
    memories = nexus_recall(body.message, body.user_id, key, db, 3)
    results["memex"] = memories
    oracle = oracle_predict_intent(body.message, body.user_id, key, db)
    results["oracle"] = oracle
    lens = lens_build_context_prompt(body.message, body.user_id, key, db)
    results["lens"] = lens
    genesis = genesis_process(body.message, key, db)
    results["genesis_prime"] = {"coherence_score": genesis.get("coherence_score"), "understanding_level": genesis.get("understanding_level")}
    empathon = empathon_read_emotional_reality(body.message, key, db)
    results["empathon"] = {"emotional_state": empathon.get("emotional_state"), "what_is_needed": empathon.get("what_is_needed")}
    if body.response:
        sentinel = sentinel_check_response(body.response, key, db)
        results["sentinel"] = sentinel
        truth = truthfield_verify(body.response, key, db)
        results["truthfield"] = {"integrity_score": truth.get("structural_integrity_score"), "is_honest": truth.get("is_structurally_honest")}
        if sentinel.get("is_safe"):
            nexus_remember(f"User: {body.message[:100]}", body.user_id, key, db)
            flux_store_cache(body.message, body.response, key, db)
            insight_track(body.message, body.response, body.user_id, key, db, 0.0)
        if body.target_language and body.target_language != "en":
            translated = atlas_translate(body.response, body.target_language, key, db)
            results["atlas"] = translated
    return {
        "blocked": False,
        "cache_hit": False,
        "context": lens.get("context_prompt", ""),
        "intent": oracle.get("predicted_intent"),
        "memory_count": memories.get("count", 0),
        "understanding": genesis.get("understanding_level", "surface"),
        "emotional_state": empathon.get("emotional_state", "neutral"),
        "results": results
    }
