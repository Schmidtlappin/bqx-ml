# BQX ML Documentation Index

**Last Updated:** 2025-11-14
**Active Documents:** 35
**Archived Documents:** 92 (see [archive_2025_11_14/](archive_2025_11_14/), [archive_2025_11_12/](archive_2025_11_12/))

---

## Quick Navigation

- [Current Status & Issues](#current-status--issues)
- [Infrastructure & Architecture](#infrastructure--architecture)
- [Phase 2 Execution](#phase-2-execution)
- [Phase 3 Planning](#phase-3-planning)
- [Phase 1 Completion](#phase-1-completion)
- [Intelligence & Analysis](#intelligence--analysis)
- [Archive Policy](#archive-policy)

---

## Current Status & Issues

### Active Issues & Remediation
**[known_issues_and_remediation_2025_11_14.md](known_issues_and_remediation_2025_11_14.md)** ⭐ **READ FIRST**
- Current blockers and remediation plans
- 7 identified issues with severity ratings
- Remediation timelines and owners
- Critical path analysis

**Historical:**
- [known_issues_current_state.md](known_issues_current_state.md) - Superseded by 2025-11-14 version
- [known_issues_and_remediation_archived_2025_11_13_morning.md](known_issues_and_remediation_archived_2025_11_13_morning.md)
- [phase_2_issues_remediated.md](phase_2_issues_remediated.md)

---

## Infrastructure & Architecture

### Current Architecture (Temporary EC2)
**[REFACTORED_PLAN_SUMMARY.md](REFACTORED_PLAN_SUMMARY.md)** ⭐ **PRIMARY REFERENCE**
- Complete refactoring from in-place upgrade to temporary EC2
- Cost analysis and ROI
- Implementation steps
- Annual savings: $2,737/year

**[architecture_decision_temporary_ec2.md](architecture_decision_temporary_ec2.md)**
- Full rationale for temporary EC2 approach
- Comparison: In-place vs Temporary EC2
- Technical requirements
- Risk assessment

**[temporary_ec2_implementation_guide.md](temporary_ec2_implementation_guide.md)**
- Quick reference implementation guide
- 5-step process
- Troubleshooting guide
- Architecture diagrams

**[phase_2_ec2_cost_analysis.md](phase_2_ec2_cost_analysis.md)**
- Detailed cost breakdown
- Multiple scenario analysis
- TCO (Total Cost of Ownership) over 1-5 years

### System Architecture
**[architecture.md](architecture.md)**
- Overall system architecture
- Aurora PostgreSQL Serverless v2
- EC2 infrastructure
- Data flow diagrams

**[trillium_master_readiness.md](trillium_master_readiness.md)**
- Current EC2 instance status
- Track 2 completion verification
- System readiness for Phase 2

---

## Phase 2 Execution

### Execution Plans
**[phase_2_next_steps_recommendations.md](phase_2_next_steps_recommendations.md)** ⭐ **NEXT STEPS**
- Comprehensive Phase 2 next steps
- Infrastructure setup
- Worker script development
- Validation and monitoring

**[phase_2_execution_guide.md](phase_2_execution_guide.md)**
- Step-by-step execution guide
- Parallel track coordination
- Monitoring commands
- Success criteria

**[phase_2_parallel_execution_plan.md](phase_2_parallel_execution_plan.md)**
- Detailed parallel execution strategy
- Resource allocation (8 cores, 2 cores, etc.)
- Timeline estimation
- Dependencies

### Data & Gap Analysis
**[phase_2_comprehensive_gap_analysis.md](phase_2_comprehensive_gap_analysis.md)**
- Complete gap analysis for Phase 2
- Missing features identified
- Remediation strategies

**[phase_2_data_gap_analysis_and_optimization.md](phase_2_data_gap_analysis_and_optimization.md)**
- Data quality assessment
- Optimization opportunities
- Schema improvements

**[airtable_phase_2_verification.md](airtable_phase_2_verification.md)**
- AirTable project plan verification
- Stage completeness checks
- Timeline validation

### Feature Engineering
**[phase_2_feature_engineering_plan.md](phase_2_feature_engineering_plan.md)**
- 1080 features specification
- Track 2 (Regression) breakdown
- Stages 2.2-2.9 feature sets

**[phase_2_feature_engineering_summary.md](phase_2_feature_engineering_summary.md)**
- Feature engineering overview
- Implementation patterns
- Quality metrics

**[comprehensive_feature_development_plan.md](comprehensive_feature_development_plan.md)**
- All Phase 1-3 features
- Feature dependencies
- Implementation priorities

**[comprehensive_feature_inventory.md](comprehensive_feature_inventory.md)**
- Complete feature catalog
- Coverage verification
- Feature metadata

### Track 1 & Track 2
**[track_1_unblocked_features_specification.md](track_1_unblocked_features_specification.md)**
- Track 1 features (already complete)
- Technical specifications
- Verification status

**[track_2_optimization_analysis.md](track_2_optimization_analysis.md)**
- Track 2 (Regression) optimization
- Performance analysis
- Completed 2025-11-13

### Execution Plans (Phase 2.1)
**[phase_2_1_execution_plan_from_audit.md](phase_2_1_execution_plan_from_audit.md)**
- Stage 2.1 execution audit
- Lessons learned
- Best practices

---

## Phase 3 Planning

### SageMaker Deployment
**[sagemaker_phase3_deployment_plan.md](sagemaker_phase3_deployment_plan.md)** ⭐ **PHASE 3 PRIMARY**
- Complete SageMaker architecture
- Deployment strategy
- Cost estimates
- Timeline

**[sagemaker_phase3_reconciled_1080_features.md](sagemaker_phase3_reconciled_1080_features.md)**
- Feature reconciliation for SageMaker
- 1080 features mapped to ML pipeline
- Feature engineering for training

**[bqx_ml_sagemaker_integration_summary.md](bqx_ml_sagemaker_integration_summary.md)**
- Integration summary
- Architecture decisions
- Implementation steps

---

## Phase 1 Completion

### Completion Summaries
**[phase_1_completion_summary.md](phase_1_completion_summary.md)**
- Phase 1 final status
- All stages completed
- Handoff to Phase 2

**[airtable_operational_cadence.md](airtable_operational_cadence.md)**
- Operational cadence established
- AirTable update procedures
- Reporting standards

### Stage Execution Reports
**[phase_1_6_remaining_execution_plan.md](phase_1_6_remaining_execution_plan.md)**
- Stage 1.6 completion plan
- Remaining features

**[phase_1_8_execution_plan.md](phase_1_8_execution_plan.md)**
- Stage 1.8 execution

**[phase_1_9_final_features_plan.md](phase_1_9_final_features_plan.md)**
- Stage 1.9 final features

**[stage_1_5_2_verification.md](stage_1_5_2_verification.md)**
- Stage 1.5.2 verification results

**[stage_1_5_3_summary.md](stage_1_5_3_summary.md)**
- Stage 1.5.3 completion

**[stage_1_5_4_5_progress_report.md](stage_1_5_4_5_progress_report.md)**
- Stages 1.5.4-1.5.5 progress

**[stage_1_5_4_status.md](stage_1_5_4_status.md)**
- Stage 1.5.4 status

**[stage_1_5_5_summary.md](stage_1_5_5_summary.md)**
- Stage 1.5.5 completion

**[stage_1_6_9_execution_report.md](stage_1_6_9_execution_report.md)**
- Stage 1.6.9 execution report

---

## Intelligence & Analysis

### Intelligence Files
**[intelligence/](intelligence/)** - Directory of analysis and intelligence files
- Feature analysis
- Performance metrics
- Optimization recommendations

### Gap Assessments
**[gap_assessments/](gap_assessments/)** - Historical gap analysis directory
- Early phase gap analyses
- Remediation tracking

### Issue Tracking
**[issues/](issues/)** - Historical issue tracking directory
- Resolved issues
- Lessons learned

---

## User Expectations & Operations

**[USER-EXPECTATIONS-BQX-ML.md](USER-EXPECTATIONS-BQX-ML.md)**
- Complete user expectations document
- Requirements specification
- Success criteria

**[BQX ML User Expectations 2025 1112.docx](BQX%20ML%20User%20Expectations%202025%201112.docx)**
- Original requirements document

**[OPERATIONAL-CADENCE.md](OPERATIONAL-CADENCE.md)**
- Operational procedures
- Update schedules
- Communication protocols

**[OPERATIONAL-CADENCE-SUMMARY.txt](OPERATIONAL-CADENCE-SUMMARY.txt)**
- Quick reference summary

**[BQX-ML-REPOSITORY-MIGRATION-COMPLETE.md](BQX-ML-REPOSITORY-MIGRATION-COMPLETE.md)**
- Repository migration completion
- Post-migration verification

**[CRITICAL_GAPS_AND_NEXT_ACTIONS.md](CRITICAL_GAPS_AND_NEXT_ACTIONS.md)**
- Historical gaps (mostly resolved)
- Next actions archive

---

## Archive Policy

### When to Archive
Documents are archived when:
1. Superseded by newer plans (e.g., old Phase 2 execution plans)
2. Phase completion (e.g., Phase 1 interim reports)
3. Historical reference only (e.g., early architecture iterations)
4. Consolidated into comprehensive docs

### Archive Directories
- **[archive_2025_11_14/](archive_2025_11_14/)** - November 14, 2025 archive (46 files)
  - Pre-temporary EC2 architecture docs
  - Superseded gap analyses
  - Consolidated feature plans
  - Interim verification reports

- **[archive_2025_11_12/](archive_2025_11_12/)** - November 12, 2025 archive (46 files)
  - Historical Phase 1 planning
  - Early refactoring plans

### Archive Contents
See individual archive directories for detailed manifests.

---

## Documentation Best Practices

### Naming Conventions
- **Phase X** - Major project phases (1, 2, 3)
- **Stage X.Y** - Sub-stages within phases
- **Track X** - Parallel execution tracks
- **_plan** - Forward-looking planning documents
- **_summary** - Completion/recap documents
- **_analysis** - Deep-dive technical analysis
- **_verification** - Validation and QA documents

### Update Frequency
- **Issues & Remediation:** Daily during active development
- **Execution Plans:** Updated at phase transitions
- **Architecture Decisions:** Versioned with date stamps
- **Summaries:** Created at stage/phase completion

### Markdown Standards
- Include "Last Updated" date in header
- Use clear section hierarchy (##, ###, ####)
- Include quick navigation for long docs
- Use tables for comparisons
- Include code blocks with language tags
- Link to related documents

---

## Quick Links

### External Resources
- **AirTable Project Plan:** https://airtable.com/appR3PPnrNkVo48mO
- **Aurora Cluster:** trillium-bqx-cluster.cluster-cgb6gegwk5qz.us-east-1.rds.amazonaws.com
- **EC2 Console:** https://console.aws.amazon.com/ec2/home?region=us-east-1
- **Service Quotas:** https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas/L-1216C47A

### Scripts
- **Infrastructure:** [/scripts/infrastructure/](../scripts/infrastructure/)
- **AirTable Updates:** [/scripts/airtable/](../scripts/airtable/)
- **ML Workers:** [/scripts/ml/](../scripts/ml/)
- **Orchestration:** [/scripts/orchestration/](../scripts/orchestration/)

---

## Contact & Support

For questions or updates, refer to:
1. [known_issues_and_remediation_2025_11_14.md](known_issues_and_remediation_2025_11_14.md) - Current blockers
2. [REFACTORED_PLAN_SUMMARY.md](REFACTORED_PLAN_SUMMARY.md) - Current architecture
3. [phase_2_next_steps_recommendations.md](phase_2_next_steps_recommendations.md) - Next actions

---

**Documentation Maintained By:** Infrastructure & ML Engineering Teams
**Last Major Update:** 2025-11-14 (Temporary EC2 architecture)
**Next Review:** 2025-11-15 (Post-quota approval)
