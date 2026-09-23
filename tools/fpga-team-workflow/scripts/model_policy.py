"""Local policy routing only. This module never changes any model settings."""
from datetime import datetime, timezone
from ftw_common import PACKAGE, Refusal, digest, read, require_schema, result

EFFORTS = {'low', 'medium', 'high', 'xhigh', 'max', 'ultra'}

def validate_policy(policy):
    require_schema(policy)
    if policy.get('mode') not in {'recommend_only', 'apply_authorized'}:
        raise Refusal('Unknown model policy mode')
    if not policy.get('policy_version'):
        raise Refusal('Missing policy_version')
    profiles, catalog = policy.get('routing_profiles', {}), policy.get('catalog', {})
    for name in ('execution', 'routine', 'analysis', 'decision', 'deep'):
        if name not in profiles:
            raise Refusal('Missing routing profile: ' + name)
        p = profiles[name]
        c = catalog.get(p.get('model_ref'))
        if not c or not c.get('model_id'):
            raise Refusal('Unknown model_ref: ' + name)
        effort = p.get('reasoning_effort')
        if effort not in EFFORTS or effort not in c.get('candidate_efforts', []):
            raise Refusal('Unsupported policy effort: ' + str(effort))
    quality = policy.get('quality_status', 'UNBENCHMARKED')
    if quality not in {'UNBENCHMARKED', 'VALIDATED_FOR_SCOPE', 'REJECTED_FOR_SCOPE'}:
        raise Refusal('Unknown quality status')
    if quality != 'UNBENCHMARKED' and (not policy.get('calibration_ref') or not policy.get('calibration_scope')):
        raise Refusal('Calibration scope and evidence required')

def stop_reason(task):
    # task.repair is a VIEW of the original findings ledger, never a resettable local counter.
    repair = task.get('repair', {})
    if repair.get('rounds', 0) >= 3 or repair.get('consecutive_no_progress', 0) >= 2:
        return 'Repair limit reached; preserve original finding ID and stop automatic repair'
    if task.get('missing_conditions'):
        return 'Missing real conditions: ' + ', '.join(task['missing_conditions'])
    if task.get('blocking_counterexample'):
        return 'Existing counterexample already blocks acceptance; no costly rerun or model vote'
    return None

def choose_profile(task):
    phase = task.get('phase', 'implementation')
    facts = {**task, **task.get('phase_facts', {}).get(phase, {})}
    activity = facts.get('activity', 'unknown')
    if facts.get('complex_cross_layer') and facts.get('specific_uncertainty'):
        return 'deep', facts['specific_uncertainty']
    if facts.get('assumption_conflict') or facts.get('public_interface') or facts.get('cross_clock') or facts.get('high_impact') or activity == 'architecture':
        return 'decision', 'Key assumptions, public interfaces, or high-impact decisions need independent analysis'
    if not facts.get('contract_trusted', False):
        return 'decision', 'Contract or acceptance basis is not yet trusted; confirm original evidence first'
    if activity in {'diagnosis', 'checker_design', 'reference_design', 'review'} or phase == 'review':
        return 'analysis', 'Bounded diagnosis, verification design, or independent review'
    if activity == 'fixed_execution' and facts.get('trusted_entry'):
        return 'execution', 'Trusted fixed entry; scripts first'
    if activity in {'implementation', 'proven_local_fix', 'documentation'}:
        return 'routine', 'Trusted contract and bounded implementation'
    return 'analysis', 'Activity needs clarification; no low-cost assumption from title alone'

def availability(pair, capabilities, actor):
    if not capabilities:
        return 'UNKNOWN', 'No observed member capability record'
    require_schema(capabilities)
    if capabilities.get('actor_ref') != actor or not capabilities.get('source_ref'):
        return 'UNKNOWN', 'Capability record lacks actor-bound provenance'
    checked = capabilities.get('checked_at')
    try:
        dt = datetime.fromisoformat(checked.replace('Z', '+00:00'))
        age = (datetime.now(timezone.utc) - dt).total_seconds()
        if age < -300 or age > capabilities.get('max_age_hours', 24) * 3600:
            return 'UNKNOWN', 'Capability record stale or future dated'
    except (AttributeError, TypeError, ValueError):
        return 'UNKNOWN', 'Capability check time unknown'
    efforts = capabilities.get('models', {}).get(pair['model_id'])
    if efforts is None:
        return ('UNAVAILABLE' if capabilities.get('complete') else 'UNKNOWN'), 'Model not in observed list'
    return ('AVAILABLE' if pair['reasoning_effort'] in efforts else 'UNAVAILABLE'), 'Actor-bound capability record'

def inspect_settings(metadata=None, roles=(), requested=None):
    # A file is an evidence reference, not an authenticated client adapter.
    observed = {'main': {'model_id': None, 'reasoning_effort': None,
                          'observation_status': 'UNKNOWN', 'evidence_ref': None}, 'subagents': []}
    conflicts = []
    if metadata:
        require_schema(metadata)
        for key in ('main', 'subagents'):
            records = [metadata.get(key, {})] if key == 'main' else metadata.get(key, [])
            for item in records:
                if not item or (key == 'subagents' and not item.get('started')):
                    continue
                kind = item.get('source_kind')
                status = 'USER_REPORTED' if kind == 'user_report' else 'UNKNOWN'
                # No VERIFIED state without a real, separately implemented client adapter.
                item = {**item, 'observation_status': status,
                        'verification_limit': 'Imported metadata is not independently authenticated'}
                if requested and status == 'USER_REPORTED' and any(item.get(k) != requested.get(k) for k in ('model_id', 'reasoning_effort')):
                    item['observation_status'] = 'MISMATCH'
                if key == 'main': observed[key] = item
                else: observed[key].append(item)
    import tomllib
    for role in roles:
        data = tomllib.loads(role.read_text(encoding='utf-8-sig'))
        pair = {'model_id': data.get('model'), 'reasoning_effort': data.get('model_reasoning_effort')}
        if any(pair.values()):
            conflicts.append({'role': role.stem, **pair, 'source_ref': str(role),
                              'kind': 'CONFIGURED_OVERRIDE_NOT_OBSERVED',
                              'differs_from_requested': bool(requested and any(pair[k] and pair[k] != requested.get(k) for k in pair))})
    return result(observed=observed, role_overrides=conflicts, settings_modified=False,
                  runtime_adapter='UNSUPPORTED', requested=requested)

def recommend(config, task, capabilities=None):
    require_schema(config)
    require_schema(task)
    policy = config.get('model_policy')
    configured = policy is not None
    if policy is None:
        policy = read(PACKAGE/'assets/project.example.yaml')['model_policy']
    validate_policy(policy)
    kind = task.get('execution_kind', 'model_assisted')
    if kind not in {'script_only', 'human_only', 'model_assisted'}:
        raise Refusal('Unknown execution_kind')
    if kind != 'model_assisted' and task.get('requires_engineering_reasoning'):
        raise Refusal('Non-model label cannot bypass required engineering reasoning')
    profile, reason = choose_profile(task)
    rec = {'routing_profile': None, 'model_id': None, 'reasoning_effort': None,
           'reason': 'Not applicable: ' + kind} if kind != 'model_assisted' else {
        'routing_profile': profile,
        'model_id': policy['catalog'][policy['routing_profiles'][profile]['model_ref']]['model_id'],
        'reasoning_effort': policy['routing_profiles'][profile]['reasoning_effort'], 'reason': reason}
    rec['escalation_triggers'] = ['New interface/clock/cross-layer impact', 'Contradictory reference or assumptions',
                                  'First no-progress round: recheck root cause; limits never reset']
    av, av_reason = availability(rec, capabilities, task.get('actor_ref')) if kind == 'model_assisted' else ('NOT_APPLICABLE', kind)
    stop = stop_reason(task)
    chosen = task.get('user_choice')
    if chosen:
        model = next((v for v in policy['catalog'].values() if v['model_id'] == chosen.get('model_id')), None)
        if not model or chosen.get('reasoning_effort') not in model['candidate_efforts']:
            raise Refusal('User choice is not in the verified policy candidate set; maintain policy first')
    alternatives = []
    for candidate in policy.get('approved_alternatives', {}).get(profile, []):
        if not candidate.get('quality_evidence_ref'):
            continue
        if availability(candidate, capabilities, task.get('actor_ref'))[0] == 'AVAILABLE':
            alternatives.append(candidate)
    status = 'BLOCKED' if stop else 'NEEDS_USER_ACTION' if av == 'UNAVAILABLE' else 'OK'
    return result(status, task_ref=task.get('task_ref'), actor_ref=task.get('actor_ref'),
                  base_commit=task.get('base_commit'), phase=task.get('phase', 'implementation'),
                  execution_kind=kind, policy_configured=configured, policy_version=policy['policy_version'],
                  policy_content_sha256=digest(policy), recommended=rec,
                  availability_status=av, availability_reason=av_reason, alternatives=alternatives,
                  quality_status=policy.get('quality_status', 'UNBENCHMARKED'),
                  requested=chosen, observed=inspect_settings()['observed'],
                  application_status='USER_SELECTED' if chosen else 'RECOMMENDATION_ONLY',
                  settings_modified=False, stop_reason=stop, repair=task.get('repair', {}),
                  usage={'metric_kind': None, 'value': None, 'source_ref': None},
                  manual_path='Desktop: model/effort control below composer; CLI: /model. Confirm available pair; no automatic application.')
