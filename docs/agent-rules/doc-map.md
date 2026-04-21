# AI Doc Map Manifest

manifest_version: 1
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
  - id: hld_overview
    path: docs/backend/HLD/00-overview-and-problem.md
    purpose: backend matching goals and architecture scope
    triggers: [architecture_context, onboarding_matching]

  - id: hld_architecture
    path: docs/backend/HLD/10-architecture-overview.md
    purpose: backend layer boundaries and component integration
    triggers: [refactor_planning, component_ownership]

  - id: hld_pipeline
    path: docs/backend/HLD/20-matching-pipeline.md
    purpose: matching stages, scoring weights, fallback behavior
    triggers: [ranking_change, retrieval_logic, llm_evaluation]

  - id: hld_storage
    path: docs/backend/HLD/30-data-and-storage.md
    purpose: Mongo and Chroma ownership, sync boundaries
    triggers: [data_model_change, persistence_change, consistency_review]

  - id: hld_runtime_api
    path: docs/backend/HLD/40-api-and-runtime-flows.md
    purpose: matching endpoints and execution/query runtime flows
    triggers: [api_contract_change, runtime_flow_change]

loading_walkthrough:
  step_0: read_AGENTS_and_agent_rules_in_startup_order
  step_1: classify_task_type_using_playbook
  step_2: load_target_docs_from_task_router
  step_3: if_task_touches_multiple_domains_union_all_target_docs
  step_4: if_task_is_unclear_load_hld_overview_then_reclassify
  step_5: if_no_router_match_default_to_architecture_review
  step_6: do_not_load_unmapped_docs_unless_required_by_conflict_or_error

load_profiles:
  minimal_api_change:
    when: API_contract_change
    load:
      - docs/backend/HLD/40-api-and-runtime-flows.md
      - docs/backend/HLD/10-architecture-overview.md

  minimal_matching_change:
    when: Matching_logic_change
    load:
      - docs/backend/HLD/20-matching-pipeline.md
      - docs/backend/HLD/30-data-and-storage.md

  minimal_data_change:
    when: Data_model_change
    load:
      - docs/backend/HLD/30-data-and-storage.md
      - docs/backend/HLD/40-api-and-runtime-flows.md

  full_architecture_review:
    when: Architecture_review
    load:
      - docs/backend/HLD/00-overview-and-problem.md
      - docs/backend/HLD/10-architecture-overview.md
      - docs/backend/HLD/20-matching-pipeline.md
      - docs/backend/HLD/30-data-and-storage.md
      - docs/backend/HLD/40-api-and-runtime-flows.md

task_router:
  API_contract_change: [hld_runtime_api, hld_architecture]
  Matching_logic_change: [hld_pipeline, hld_storage]
  Data_model_change: [hld_storage, hld_runtime_api]
  Architecture_review: [hld_overview, hld_architecture, hld_pipeline, hld_storage, hld_runtime_api]

constraints:
  - use_paths_as_source_of_truth
  - do_not_infer_missing_docs
  - if_conflict_follow_rule_priority_in_AGENTS
