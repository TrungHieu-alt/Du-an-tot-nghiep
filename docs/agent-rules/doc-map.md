# AI Doc Map Manifest

manifest_version: 3
intent: agent-only navigation and routing for project documentation
human_mode: false

read_order:
  - AGENTS.md
  - docs/agent-rules/quick-context.md
  - docs/agent-rules/codemap.md
  - docs/agent-rules/doc-map.md
  - docs/agent-rules/playbook.md
  - docs/agent-rules/definition-of-done.md
  - docs/agent-rules/working-contract.md

doc_nodes:
  - id: requirements
    path: docs/REQUIREMENTS.md
    purpose: high-level product spec — what we build, why, constraints, acceptance criteria, data model, scoring formula
    triggers: [new_feature, behavior_change, domain_logic_change, test_writing, pr_review, ambiguity_resolution]
  - id: app_overview
    path: docs/backend/HLD/00-overview-and-problem.md
    purpose: MVP backend goals, users, scope, and legacy prototype gap
    triggers: [architecture_context, onboarding, planning]
  - id: app_architecture
    path: docs/backend/HLD/10-architecture-overview.md
    purpose: backend layers, components, boundaries, and ownership
    triggers: [architecture_review, refactor_planning, component_ownership]
  - id: app_ingestion
    path: docs/backend/HLD/20-ingestion-and-normalization.md
    purpose: upload, object storage, text extraction, preprocessing, LLM parse, embedding lifecycle
    triggers: [ingestion_change, upload_flow, parsing_change, embedding_generation]
  - id: app_storage
    path: docs/backend/HLD/30-data-and-storage.md
    purpose: PostgreSQL, object storage, pgvector, entity invariants
    triggers: [data_model_change, persistence_change, consistency_review]
  - id: app_matching_search
    path: docs/backend/HLD/40-matching-and-search-pipeline.md
    purpose: matching eligibility, hard filters, scoring, reranking, reasoning, keyword vs semantic search
    triggers: [matching_logic_change, search_change, ranking_change, retrieval_logic]
  - id: app_runtime_api
    path: docs/backend/HLD/50-api-and-runtime-flows.md
    purpose: API namespaces, runtime flows, OpenAPI contract expectations
    triggers: [api_contract_change, runtime_flow_change, frontend_integration]
  - id: app_api_contract_lld
    path: docs/backend/LLD/40-api-contract.md
    purpose: endpoint-level API contract, schemas, auth, errors, side effects, and OpenAPI implementation checklist
    triggers: [api_contract_change, openapi_contract, frontend_integration]
  - id: app_security_audit
    path: docs/backend/HLD/60-security-notifications-audit.md
    purpose: auth, authorization, privacy, notifications, audit, observability
    triggers: [auth_change, security_change, notification_change, audit_change, admin_monitoring]
  - id: legacy_matching_pipeline
    path: docs/backend/HLD/legacy/legacy-matching-pipeline.md
    purpose: legacy V2 prototype deterministic matching formula and migration test reference
    triggers: [legacy_reference_review]

loading_walkthrough:
  step_0: read_AGENTS_and_agent_rules_in_startup_order
  step_1: classify_task_type_using_playbook
  step_2: load_target_docs_from_task_router
  step_3: if_task_touches_multiple_domains_union_all_target_docs
  step_4: if_task_is_unclear_load_app_overview_then_reclassify
  step_5: if_no_router_match_default_to_architecture_review
  step_6: load_legacy_docs_only_when_task_explicitly_targets_legacy_reference_review
  step_7: do_not_load_unmapped_docs_unless_required_by_conflict_or_error

load_profiles:
  minimal_api_change:
    when: API_contract_change
    load:
      - docs/backend/HLD/50-api-and-runtime-flows.md
      - docs/backend/LLD/40-api-contract.md
      - docs/backend/HLD/10-architecture-overview.md
  minimal_matching_change:
    when: Matching_logic_change
    load:
      - docs/backend/HLD/40-matching-and-search-pipeline.md
      - docs/backend/HLD/30-data-and-storage.md
  minimal_data_change:
    when: Data_model_change
    load:
      - docs/backend/HLD/30-data-and-storage.md
      - docs/backend/HLD/50-api-and-runtime-flows.md
  minimal_ingestion_change:
    when: Ingestion_or_parse_change
    load:
      - docs/backend/HLD/20-ingestion-and-normalization.md
      - docs/backend/HLD/30-data-and-storage.md
      - docs/backend/HLD/50-api-and-runtime-flows.md
      - docs/backend/LLD/40-api-contract.md
  minimal_security_change:
    when: Auth_security_notification_or_audit_change
    load:
      - docs/backend/HLD/60-security-notifications-audit.md
      - docs/backend/HLD/50-api-and-runtime-flows.md
      - docs/backend/LLD/40-api-contract.md
  full_architecture_review:
    when: Architecture_review
    load:
      - docs/backend/HLD/00-overview-and-problem.md
      - docs/backend/HLD/10-architecture-overview.md
      - docs/backend/HLD/20-ingestion-and-normalization.md
      - docs/backend/HLD/30-data-and-storage.md
      - docs/backend/HLD/40-matching-and-search-pipeline.md
      - docs/backend/HLD/50-api-and-runtime-flows.md
      - docs/backend/LLD/40-api-contract.md
      - docs/backend/HLD/60-security-notifications-audit.md
  legacy_prototype_reference:
    when: Legacy_reference_review
    load:
      - docs/backend/HLD/legacy/legacy-matching-pipeline.md
      - docs/backend/HLD/legacy/legacy-data-and-storage.md
      - docs/backend/HLD/legacy/legacy-api-and-runtime-flows.md
      - docs/matching-v2-scenario-test-cases.md

task_router:
  API_contract_change: [requirements, app_runtime_api, app_api_contract_lld, app_architecture]
  Matching_logic_change: [requirements, app_matching_search, app_storage]
  Search_change: [requirements, app_matching_search, app_runtime_api, app_api_contract_lld]
  Data_model_change: [requirements, app_storage, app_runtime_api]
  Ingestion_or_parse_change: [requirements, app_ingestion, app_storage, app_runtime_api, app_api_contract_lld]
  Auth_security_notification_or_audit_change: [requirements, app_security_audit, app_runtime_api, app_api_contract_lld]
  Application_or_invite_change: [requirements, app_storage, app_runtime_api, app_api_contract_lld, app_security_audit]
  Architecture_review: [requirements, app_overview, app_architecture, app_ingestion, app_storage, app_matching_search, app_runtime_api, app_api_contract_lld, app_security_audit]
  New_feature: [requirements, app_overview]
  Behavior_change: [requirements]
  Domain_logic_change: [requirements]
  Legacy_reference_review: [requirements, legacy_matching_pipeline]

constraints:
  - use_paths_as_source_of_truth
  - do_not_infer_missing_docs
  - hld_is_target_architecture_not_current_runtime
  - legacy_prototype_docs_are_reference_only_not_current_runtime
  - if_conflict_follow_rule_priority_in_AGENTS
