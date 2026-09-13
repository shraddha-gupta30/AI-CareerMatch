"""
Skill Gap Analysis and What-If Career Simulator Service.
Encapsulates 100% deterministic calculation of skill gaps, experience gaps,
education compatibility, and in-memory what-if simulations.

Single source of truth for match scoring remains `calculate_job_match()` in `matching_engine.py`.
Zero persistence or mutation occurs during simulations.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.job import Job
from app.models.profile import CandidateProfile
from app.schemas.gap import (
    EducationCompatibilityResponse,
    ExperienceGapDetail,
    MatchedSkillItem,
    MissingSkillItem,
    PartialSkillItem,
    SimulationRequest,
    SimulationResponse,
    SkillGapResponse,
)
from app.schemas.job import JobMatchBreakdownResponse
from app.services.matching_engine import JobMatchResult, calculate_job_match


class SimulatedCandidateSkill:
    """Lightweight in-memory representation of a candidate skill for simulation."""
    def __init__(
        self,
        name: str,
        proficiency_level: str = "intermediate",
        proficiency_source: str = "user_verified",
        years_experience: float = 1.0,
    ):
        self.name = name
        self.proficiency_level = proficiency_level
        self.proficiency_source = proficiency_source
        self.years_experience = years_experience


class SimulatedCandidateProfile:
    """Lightweight in-memory candidate profile that mimics CandidateProfile attributes."""
    def __init__(
        self,
        skills: List[Any],
        total_experience_years: float,
        education: List[Any],
    ):
        self.skills = skills
        self.total_experience_years = total_experience_years
        self.education = education


def derive_skill_gaps(
    profile: CandidateProfile,
    job: Job,
    rel_map: Dict[str, Dict[str, float]],
    alias_map: Dict[str, str],
) -> SkillGapResponse:
    """
    Computes a deterministic skill gap analysis for an authenticated candidate against a job posting.
    Categorizes skills into matched required, partial required, missing required,
    matched preferred, partial preferred, missing preferred, experience gap, and education compatibility.
    """
    match_result: JobMatchResult = calculate_job_match(profile, job, rel_map, alias_map)

    # Categorize matched skills
    matched_required = [
        MatchedSkillItem(**s) for s in match_result.matched_skills if s.get("is_required", True)
    ]
    matched_preferred = [
        MatchedSkillItem(**s) for s in match_result.matched_skills if not s.get("is_required", True)
    ]

    # Categorize partially matched skills
    partial_required = [
        PartialSkillItem(**s) for s in match_result.partial_skills if s.get("is_required", True)
    ]
    partial_preferred = [
        PartialSkillItem(**s) for s in match_result.partial_skills if not s.get("is_required", True)
    ]

    # Categorize missing skills
    missing_required = [
        MissingSkillItem(**s) for s in match_result.missing_required_skills
    ]
    missing_preferred = [
        MissingSkillItem(**s) for s in match_result.missing_preferred_skills
    ]

    # Experience gap detail
    cand_exp = float(getattr(profile, "total_experience_years", 0.0) or 0.0)
    job_min_exp = float(getattr(job, "min_experience_years", 0.0) or 0.0)
    exp_gap_detail = ExperienceGapDetail(
        candidate_experience_years=cand_exp,
        job_min_experience_years=job_min_exp,
        experience_gap=match_result.experience_gap,
        experience_gap_text=match_result.experience_gap_text,
        experience_score=match_result.experience_score,
    )

    # Education compatibility response
    edu_resp = EducationCompatibilityResponse(**match_result.education_compatibility)

    return SkillGapResponse(
        job_id=job.id,
        overall_score=match_result.overall_score,
        required_skills_score=match_result.required_skills_score,
        preferred_skills_score=match_result.preferred_skills_score,
        experience_score=match_result.experience_score,
        education_score=match_result.education_score,
        matched_required_skills=matched_required,
        partial_required_skills=partial_required,
        missing_required_skills=missing_required,
        matched_preferred_skills=matched_preferred,
        partial_preferred_skills=partial_preferred,
        missing_preferred_skills=missing_preferred,
        experience_gap=exp_gap_detail,
        education_compatibility=edu_resp,
        total_required_skills_count=match_result.total_required_skills_count,
        matched_required_skills_count=match_result.matched_required_skills_count,
        total_preferred_skills_count=match_result.total_preferred_skills_count,
        matched_preferred_skills_count=match_result.matched_preferred_skills_count,
        active_weights=match_result.active_weights,
        explanation=match_result.explanation,
    )


def run_what_if_simulation(
    profile: CandidateProfile,
    job: Job,
    simulation_request: SimulationRequest,
    rel_map: Dict[str, Dict[str, float]],
    alias_map: Dict[str, str],
) -> SimulationResponse:
    """
    Executes a pure in-memory What-If Career Simulation.
    Clones the candidate's existing profile state, applies simulated modifications
    (add/modify/remove skills, adjust experience), and evaluates the score delta
    using `calculate_job_match()`.

    Strictly in-memory: Never persists, updates, or adds records to the database.
    """
    # 1. Baseline Evaluation
    base_match: JobMatchResult = calculate_job_match(profile, job, rel_map, alias_map)

    # 2. In-memory clone of candidate skills
    cloned_skills_map: Dict[str, SimulatedCandidateSkill] = {}
    existing_skills_prof_map: Dict[str, str] = {}

    for cs in getattr(profile, "skills", []) or []:
        s_obj = getattr(cs, "skill", None)
        s_name = (
            getattr(s_obj, "name", None)
            or getattr(cs, "name", None)
            or getattr(cs, "skill_name", "")
        )
        if not s_name:
            continue
        p_level = getattr(cs, "proficiency_level", "intermediate") or "intermediate"
        p_source = getattr(cs, "proficiency_source", "user_verified") or "user_verified"
        y_exp = float(getattr(cs, "years_experience", 1.0) or 1.0)

        norm_key = s_name.strip().lower()
        existing_skills_prof_map[norm_key] = str(p_level).lower()
        cloned_skills_map[norm_key] = SimulatedCandidateSkill(
            name=s_name,
            proficiency_level=str(p_level).lower(),
            proficiency_source=str(p_source).lower(),
            years_experience=y_exp,
        )

    # 3. Apply Removals
    if simulation_request.remove_skills:
        remove_set = {s.strip().lower() for s in simulation_request.remove_skills if s.strip()}
        for rm in remove_set:
            # Check direct or alias match
            keys_to_remove = [k for k, v in cloned_skills_map.items() if k == rm or v.name.lower() == rm]
            for k in keys_to_remove:
                cloned_skills_map.pop(k, None)

    # 4. Apply Modifications
    if simulation_request.modify_skills:
        for mod in simulation_request.modify_skills:
            norm = mod.name.strip().lower()
            matched_key = next((k for k, v in cloned_skills_map.items() if k == norm or v.name.lower() == norm), None)
            if matched_key:
                cloned_skills_map[matched_key].proficiency_level = mod.proficiency_level
                if mod.proficiency_source:
                    cloned_skills_map[matched_key].proficiency_source = mod.proficiency_source
            else:
                # If modifying a skill not yet in profile, treat as added
                cloned_skills_map[norm] = SimulatedCandidateSkill(
                    name=mod.name,
                    proficiency_level=mod.proficiency_level,
                    proficiency_source=mod.proficiency_source or "user_verified",
                )

    # 5. Apply Additions
    if simulation_request.add_skills:
        for add in simulation_request.add_skills:
            norm = add.name.strip().lower()
            cloned_skills_map[norm] = SimulatedCandidateSkill(
                name=add.name,
                proficiency_level=add.proficiency_level,
                proficiency_source=add.proficiency_source or "user_verified",
            )

    # 6. Apply Experience
    if simulation_request.experience_years is not None:
        sim_exp = float(simulation_request.experience_years)
    else:
        sim_exp = float(getattr(profile, "total_experience_years", 0.0) or 0.0)

    # 7. Education is preserved
    sim_edu = list(getattr(profile, "education", []) or [])

    # 8. Build Simulated Profile
    sim_profile = SimulatedCandidateProfile(
        skills=list(cloned_skills_map.values()),
        total_experience_years=sim_exp,
        education=sim_edu,
    )

    # 9. Evaluate Simulated Match
    sim_match: JobMatchResult = calculate_job_match(sim_profile, job, rel_map, alias_map)
    score_delta = round(sim_match.overall_score - base_match.overall_score, 2)

    # 10. Generate Deterministic Changed Factors Explanations
    changed_factors: List[str] = []

    # Added skills analysis
    if simulation_request.add_skills:
        for s in simulation_request.add_skills:
            m_item = next((m for m in sim_match.matched_skills if m["name"].lower() == s.name.lower()), None)
            p_item = next((p for p in sim_match.partial_skills if p["candidate_skill_name"].lower() == s.name.lower()), None)
            if m_item:
                req_type = "required" if m_item.get("is_required", True) else "preferred"
                credit_pct = int(round(m_item["credit"] * 100))
                changed_factors.append(
                    f"Added skill '{s.name}' ({s.proficiency_level}): matches {req_type} skill '{m_item['name']}' ({credit_pct}% credit)."
                )
            elif p_item:
                req_type = "required" if p_item.get("is_required", True) else "preferred"
                rel_pct = int(round(p_item["similarity_weight"] * 100))
                changed_factors.append(
                    f"Added skill '{s.name}' ({s.proficiency_level}): related to {req_type} skill '{p_item['job_skill_name']}' ({rel_pct}% partial credit)."
                )
            else:
                changed_factors.append(
                    f"Added skill '{s.name}' ({s.proficiency_level}): not explicitly requested by this job."
                )

    # Modified skills analysis
    if simulation_request.modify_skills:
        for s in simulation_request.modify_skills:
            old_prof = existing_skills_prof_map.get(s.name.strip().lower(), "unspecified")
            changed_factors.append(
                f"Modified skill '{s.name}' proficiency from '{old_prof}' to '{s.proficiency_level}'."
            )

    # Removed skills analysis
    if simulation_request.remove_skills:
        for s_name in simulation_request.remove_skills:
            was_matched = next((m for m in base_match.matched_skills if m["name"].lower() == s_name.lower()), None)
            was_partial = next((p for p in base_match.partial_skills if p["candidate_skill_name"].lower() == s_name.lower()), None)
            if was_matched:
                req_type = "required" if was_matched.get("is_required", True) else "preferred"
                changed_factors.append(
                    f"Removed skill '{s_name}': previously matched {req_type} skill '{was_matched['name']}'."
                )
            elif was_partial:
                req_type = "required" if was_partial.get("is_required", True) else "preferred"
                changed_factors.append(
                    f"Removed skill '{s_name}': previously contributed partial credit for '{was_partial['job_skill_name']}'."
                )
            else:
                changed_factors.append(
                    f"Removed skill '{s_name}'."
                )

    # Experience adjustment analysis
    if simulation_request.experience_years is not None:
        old_exp = float(getattr(profile, "total_experience_years", 0.0) or 0.0)
        new_exp = float(simulation_request.experience_years)
        if round(old_exp, 1) != round(new_exp, 1):
            changed_factors.append(
                f"Adjusted experience from {old_exp:.1f} to {new_exp:.1f} yrs (experience score: {base_match.experience_score:.1f}% -> {sim_match.experience_score:.1f}%)."
            )

    # Overall impact
    if score_delta > 0:
        changed_factors.append(
            f"Overall match score increased by +{score_delta:.2f}% ({base_match.overall_score:.1f}% -> {sim_match.overall_score:.1f}%)."
        )
    elif score_delta < 0:
        changed_factors.append(
            f"Overall match score decreased by {score_delta:.2f}% ({base_match.overall_score:.1f}% -> {sim_match.overall_score:.1f}%)."
        )
    else:
        changed_factors.append(
            f"Overall match score unchanged ({base_match.overall_score:.1f}%)."
        )

    return SimulationResponse(
        job_id=job.id,
        current_score=base_match.overall_score,
        simulated_score=sim_match.overall_score,
        score_delta=score_delta,
        current_match=JobMatchBreakdownResponse.model_validate(base_match.to_dict()),
        simulated_match=JobMatchBreakdownResponse.model_validate(sim_match.to_dict()),
        changed_factors=changed_factors,
    )
