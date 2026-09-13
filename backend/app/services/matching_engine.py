"""
Deterministic, Explainable Job Matching Engine.
Single Source of Truth for Phase 5 Match Calculations, Caching, and Simulator Scenarios.

Pure Python function: calculate_job_match(candidate_profile, job, relationships_map=None, skill_alias_map=None)
Guarantees:
- Pure deterministic repeatability (identical inputs produce identical scores)
- Zero Gemini/LLM dependency for scoring
- Bounded to [0.0, 100.0]
- Strictly adheres to approved dimension weights:
    Required skills = 0.50
    Preferred skills = 0.20
    Experience = 0.20
    Education = 0.10
- Proportional weight redistribution when a dimension is genuinely N/A
- Partial skill credit strictly governed by explicit skill_relationships
"""
from dataclasses import dataclass, field
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Set, Tuple


PROFICIENCY_RANKS: Dict[str, int] = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}

CONFIDENCE_WEIGHTS: Dict[str, float] = {
    "user_verified": 1.0,
    "resume_inferred": 0.9,
    "unknown": 0.5,
}

BASE_DIMENSION_WEIGHTS: Dict[str, float] = {
    "required_skills": 0.50,
    "preferred_skills": 0.20,
    "experience": 0.20,
    "education": 0.10,
}

EDUCATION_TIERS: Dict[str, int] = {
    "none": 0,
    "high school": 0,
    "bootcamp": 0,
    "associate": 1,
    "diploma": 1,
    "bachelor": 2,
    "master": 3,
    "doctorate": 4,
    "phd": 4,
}


@dataclass
class SkillMatchDetail:
    name: str
    candidate_proficiency: str
    required_proficiency: str
    importance_weight: float
    credit: float
    is_exact: bool
    confidence: float
    is_required: bool


@dataclass
class PartialSkillMatchDetail:
    job_skill_name: str
    candidate_skill_name: str
    similarity_weight: float
    credit: float
    candidate_proficiency: str
    required_proficiency: str
    is_required: bool


@dataclass
class MissingSkillDetail:
    name: str
    required_proficiency: str
    importance_weight: float
    is_required: bool


@dataclass
class EducationCompatibility:
    candidate_highest_level: str
    required_level: str
    meets_requirement: bool
    score: float
    explanation: str


@dataclass
class JobMatchResult:
    overall_score: float
    required_skills_score: float
    preferred_skills_score: Optional[float]
    experience_score: float
    education_score: float
    matched_skills: List[Dict[str, Any]]
    partial_skills: List[Dict[str, Any]]
    missing_required_skills: List[Dict[str, Any]]
    missing_preferred_skills: List[Dict[str, Any]]
    experience_gap: float
    experience_gap_text: str
    education_compatibility: Dict[str, Any]
    total_required_skills_count: int
    matched_required_skills_count: int
    total_preferred_skills_count: int
    matched_preferred_skills_count: int
    active_weights: Dict[str, float]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "required_skills_score": self.required_skills_score,
            "preferred_skills_score": self.preferred_skills_score,
            "experience_score": self.experience_score,
            "education_score": self.education_score,
            "matched_skills": self.matched_skills,
            "partial_skills": self.partial_skills,
            "missing_required_skills": self.missing_required_skills,
            "missing_preferred_skills": self.missing_preferred_skills,
            "experience_gap": self.experience_gap,
            "experience_gap_text": self.experience_gap_text,
            "education_compatibility": self.education_compatibility,
            "total_required_skills_count": self.total_required_skills_count,
            "matched_required_skills_count": self.matched_required_skills_count,
            "total_preferred_skills_count": self.total_preferred_skills_count,
            "matched_preferred_skills_count": self.matched_preferred_skills_count,
            "active_weights": self.active_weights,
            "explanation": self.explanation,
        }


def _parse_education_tier(text_val: Optional[str]) -> Tuple[int, str]:
    """Returns (tier_int, normalized_label) for education degrees/levels."""
    if not text_val:
        return 0, "None"
    lower = text_val.lower()

    # 1. Doctorate (Tier 4)
    if any(k in lower for k in ("phd", "doctorate", "ph.d", "doctoral", "d.phil")):
        return 4, "Doctorate"

    # 2. Master (Tier 3)
    if (
        any(k in lower for k in ("master", "m.s.", "m.tech", "mtech", "mba", "msc", "m.sc", "mca", "m.ca", "post graduate", "postgraduate"))
        or re.search(r"\b(ms|m\.s|m\.e|me)\b", lower)
    ):
        return 3, "Master"

    # 3. Bachelor (Tier 2)
    bachelor_keywords = (
        "bachelor", "b.tech", "btech", "b.e.", "bsc", "b.sc", "bca", "b.ca",
        "b.a.", "b.eng", "beng", "b.com", "bcom", "undergraduate", "b.s."
    )
    if any(k in lower for k in bachelor_keywords) or re.search(r"\b(be|b\.e|b\.s|ba|bs)\b", lower):
        return 2, "Bachelor"

    # 4. Associate / Diploma (Tier 1) - Note: ensure "high school diploma" is not counted as Associate
    if "high school" not in lower and any(k in lower for k in ("associate", "diploma", "a.s", "aas", "polytechnic")):
        return 1, "Associate"

    return 0, "High School / Certificate"


def _normalize_name(name: str) -> str:
    """Standardizes string for case/symbol insensitive lookup."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def calculate_job_match(
    candidate_profile: Any,
    job: Any,
    relationships_map: Optional[Dict[str, Dict[str, float]]] = None,
    skill_alias_map: Optional[Dict[str, str]] = None,
) -> JobMatchResult:
    """
    Pure deterministic matching function between a CandidateProfile and a Job.
    Both objects can be SQLAlchemy models or attribute-bearing objects/dicts.

    relationships_map: Dict mapping canonical skill_name (or normalized name)
                       -> { related_skill_name: similarity_weight }
    skill_alias_map: Dict mapping alias (or normalized alias) -> canonical skill_name
    """
    relationships_map = relationships_map or {}
    skill_alias_map = skill_alias_map or {}

    # -------------------------------------------------------------
    # 1. Parse Candidate Skills
    # -------------------------------------------------------------
    # candidate_skills: map from normalized skill name -> (skill_name, proficiency_rank, confidence)
    cand_skill_entries: Dict[str, Dict[str, Any]] = {}

    raw_cand_skills = getattr(candidate_profile, "skills", None) or []
    for cs in raw_cand_skills:
        # Resolve skill name from relationship, attribute, dict, or string
        s_obj = getattr(cs, "skill", None)
        s_name = (
            getattr(s_obj, "name", None)
            or getattr(cs, "name", None)
            or getattr(cs, "skill_name", "")
            or (cs.get("skill_name") or cs.get("name") if isinstance(cs, dict) else "")
            or (cs if isinstance(cs, str) else "")
        )
        if not s_name:
            continue

        # Alias resolution
        norm_s = _normalize_name(s_name)
        canonical = skill_alias_map.get(norm_s, s_name)
        norm_canonical = _normalize_name(canonical)

        prof_str = getattr(cs, "proficiency_level", "intermediate") or "intermediate"
        prof_rank = PROFICIENCY_RANKS.get(str(prof_str).lower(), 2)

        source_str = getattr(cs, "proficiency_source", "user_verified") or "user_verified"
        confidence = CONFIDENCE_WEIGHTS.get(str(source_str).lower(), 1.0)

        cand_skill_entries[norm_canonical] = {
            "name": canonical,
            "raw_name": s_name,
            "proficiency_level": str(prof_str).lower(),
            "proficiency_rank": prof_rank,
            "confidence": confidence,
        }

    # -------------------------------------------------------------
    # 2. Parse Job Skills
    # -------------------------------------------------------------
    raw_job_skills = getattr(job, "job_skills", None) or []
    req_job_skills: List[Dict[str, Any]] = []
    pref_job_skills: List[Dict[str, Any]] = []

    for js in raw_job_skills:
        s_obj = getattr(js, "skill", None)
        s_name = getattr(s_obj, "name", None) or getattr(js, "name", None) or getattr(js, "skill_name", "")
        if not s_name:
            continue

        norm_s = _normalize_name(s_name)
        canonical = skill_alias_map.get(norm_s, s_name)
        norm_canonical = _normalize_name(canonical)

        is_req = bool(getattr(js, "is_required", True))
        weight = float(getattr(js, "importance_weight", 1.0) or 1.0)
        # Enforce weight bounds [0.5, 2.0]
        weight = max(0.5, min(2.0, weight))

        min_prof_str = getattr(js, "min_proficiency", "intermediate") or "intermediate"
        min_prof_rank = PROFICIENCY_RANKS.get(str(min_prof_str).lower(), 2)

        item = {
            "name": canonical,
            "normalized_name": norm_canonical,
            "importance_weight": weight,
            "min_proficiency": str(min_prof_str).lower(),
            "min_proficiency_rank": min_prof_rank,
            "is_required": is_req,
        }
        if is_req:
            req_job_skills.append(item)
        else:
            pref_job_skills.append(item)

    # -------------------------------------------------------------
    # 3. Evaluate Skill Matching (Exact & Explicit Related Partial)
    # -------------------------------------------------------------
    matched_skills: List[Dict[str, Any]] = []
    partial_skills: List[Dict[str, Any]] = []
    missing_required_skills: List[Dict[str, Any]] = []
    missing_preferred_skills: List[Dict[str, Any]] = []

    def evaluate_skill_group(skills_list: List[Dict[str, Any]], is_required: bool) -> float:
        if not skills_list:
            return 100.0  # Handled by N/A redistribution

        total_weighted_credit = 0.0
        total_weight = 0.0

        for js in skills_list:
            w = js["importance_weight"]
            total_weight += w
            norm_target = js["normalized_name"]
            target_min_rank = js["min_proficiency_rank"]

            # A. Exact Match Check
            if norm_target in cand_skill_entries:
                cand_info = cand_skill_entries[norm_target]
                cand_rank = cand_info["proficiency_rank"]
                conf = cand_info["confidence"]

                prof_factor = min(1.0, cand_rank / target_min_rank)
                credit = round(1.0 * prof_factor * conf, 4)

                matched_skills.append({
                    "name": js["name"],
                    "candidate_proficiency": cand_info["proficiency_level"],
                    "required_proficiency": js["min_proficiency"],
                    "importance_weight": w,
                    "credit": credit,
                    "is_exact": True,
                    "confidence": conf,
                    "is_required": is_required,
                })
                total_weighted_credit += w * credit
                continue

            # B. Explicit Related Partial Match Check (strictly from relationships_map)
            best_partial_credit = 0.0
            best_partial_info: Optional[Dict[str, Any]] = None

            for norm_cand, cand_info in cand_skill_entries.items():
                cand_canonical = cand_info["name"]
                # Check candidate_skill -> job_skill or job_skill -> candidate_skill
                sim_weight = 0.0
                if cand_canonical in relationships_map and js["name"] in relationships_map[cand_canonical]:
                    sim_weight = float(relationships_map[cand_canonical][js["name"]])
                elif js["name"] in relationships_map and cand_canonical in relationships_map[js["name"]]:
                    sim_weight = float(relationships_map[js["name"]][cand_canonical])

                if sim_weight > 0.0:
                    cand_rank = cand_info["proficiency_rank"]
                    conf = cand_info["confidence"]
                    prof_factor = min(1.0, cand_rank / target_min_rank)
                    p_credit = round(sim_weight * prof_factor * conf, 4)

                    if p_credit > best_partial_credit:
                        best_partial_credit = p_credit
                        best_partial_info = {
                            "job_skill_name": js["name"],
                            "candidate_skill_name": cand_info["name"],
                            "similarity_weight": round(sim_weight, 2),
                            "credit": p_credit,
                            "candidate_proficiency": cand_info["proficiency_level"],
                            "required_proficiency": js["min_proficiency"],
                            "is_required": is_required,
                        }

            if best_partial_credit > 0.0 and best_partial_info is not None:
                partial_skills.append(best_partial_info)
                total_weighted_credit += w * best_partial_credit
            else:
                # C. Missing Skill
                missing_info = {
                    "name": js["name"],
                    "required_proficiency": js["min_proficiency"],
                    "importance_weight": w,
                    "is_required": is_required,
                }
                if is_required:
                    missing_required_skills.append(missing_info)
                else:
                    missing_preferred_skills.append(missing_info)

        if total_weight <= 0:
            return 100.0
        raw_score = (total_weighted_credit / total_weight) * 100.0
        return round(max(0.0, min(100.0, raw_score)), 2)

    has_required_skills = len(req_job_skills) > 0
    has_preferred_skills = len(pref_job_skills) > 0

    req_skills_score = evaluate_skill_group(req_job_skills, is_required=True) if has_required_skills else 100.0
    pref_skills_score = evaluate_skill_group(pref_job_skills, is_required=False) if has_preferred_skills else None

    # -------------------------------------------------------------
    # 4. Evaluate Experience
    # -------------------------------------------------------------
    cand_exp = float(getattr(candidate_profile, "total_experience_years", 0.0) or 0.0)
    job_min_exp = float(getattr(job, "min_experience_years", 0.0) or 0.0)

    if job_min_exp <= 0.0:
        exp_score = 100.0
        exp_gap = 0.0
        exp_gap_text = "Meets requirement (no prior experience required)"
    elif cand_exp >= job_min_exp:
        exp_score = 100.0
        exp_gap = 0.0
        surplus = round(cand_exp - job_min_exp, 1)
        exp_gap_text = f"Meets experience requirement (+{surplus:.1f} yr{'s' if surplus != 1.0 else ''})"
    else:
        exp_score = round(min(100.0, max(0.0, (cand_exp / job_min_exp) * 100.0)), 2)
        exp_gap = round(job_min_exp - cand_exp, 1)
        exp_gap_text = f"{exp_gap:.1f} year{'s' if exp_gap != 1.0 else ''} below requirement ({cand_exp:.1f} of {job_min_exp:.1f} yrs)"

    # -------------------------------------------------------------
    # 5. Evaluate Education Compatibility
    # -------------------------------------------------------------
    target_edu_str = getattr(job, "target_education_level", "Bachelor") or "Bachelor"
    job_edu_tier, job_edu_label = _parse_education_tier(target_edu_str)

    highest_cand_tier = 0
    highest_cand_label = "None"

    cand_education_records = getattr(candidate_profile, "education", None) or []
    for edu in cand_education_records:
        deg = getattr(edu, "degree", "") or ""
        t, label = _parse_education_tier(deg)
        if t > highest_cand_tier:
            highest_cand_tier = t
            highest_cand_label = label

    has_education_req = job_edu_tier > 0

    if not has_education_req:
        edu_score = 100.0
        edu_meets = True
        edu_expl = "No formal education level required for this role."
    elif highest_cand_tier >= job_edu_tier:
        edu_score = 100.0
        edu_meets = True
        edu_expl = f"Candidate holds {highest_cand_label}, meeting or exceeding required {job_edu_label}."
    elif highest_cand_tier == job_edu_tier - 1:
        edu_score = 75.0
        edu_meets = False
        edu_expl = f"Candidate holds {highest_cand_label} (1 tier below required {job_edu_label})."
    else:
        edu_score = 50.0 if highest_cand_tier > 0 else 40.0
        edu_meets = False
        edu_expl = f"Candidate highest education is {highest_cand_label}, below required {job_edu_label}."

    edu_compatibility = {
        "candidate_highest_level": highest_cand_label,
        "required_level": job_edu_label,
        "meets_requirement": edu_meets,
        "score": edu_score,
        "explanation": edu_expl,
    }

    # -------------------------------------------------------------
    # 6. Proportional Weight Redistribution (Active Weights Sum to 1.0)
    # -------------------------------------------------------------
    active_dims: Dict[str, float] = {}
    dim_scores: Dict[str, float] = {}

    if has_required_skills:
        active_dims["required_skills"] = BASE_DIMENSION_WEIGHTS["required_skills"]
        dim_scores["required_skills"] = req_skills_score

    if has_preferred_skills and pref_skills_score is not None:
        active_dims["preferred_skills"] = BASE_DIMENSION_WEIGHTS["preferred_skills"]
        dim_scores["preferred_skills"] = pref_skills_score

    # Experience is active unless explicitly N/A (None)
    active_dims["experience"] = BASE_DIMENSION_WEIGHTS["experience"]
    dim_scores["experience"] = exp_score

    # Education is active unless job specifies none/N/A
    if has_education_req:
        active_dims["education"] = BASE_DIMENSION_WEIGHTS["education"]
        dim_scores["education"] = edu_score

    total_active_base_weight = sum(active_dims.values())
    if total_active_base_weight <= 0:
        total_active_base_weight = 1.0
        active_dims = {"required_skills": 1.0}
        dim_scores = {"required_skills": req_skills_score}

    normalized_weights: Dict[str, float] = {
        dim: round(w / total_active_base_weight, 4)
        for dim, w in active_dims.items()
    }

    # Guarantee active weights sum to 1.0 exactly
    weight_sum = sum(normalized_weights.values())
    diff = 1.0 - weight_sum
    if abs(diff) > 1e-6:
        first_key = next(iter(normalized_weights))
        normalized_weights[first_key] = round(normalized_weights[first_key] + diff, 4)

    # Compute overall score
    overall_score = sum(normalized_weights[dim] * dim_scores[dim] for dim in normalized_weights)
    overall_score = round(max(0.0, min(100.0, overall_score)), 2)

    # Counts
    matched_req_count = len([m for m in matched_skills if m["is_required"]])
    total_req_count = len(req_job_skills)
    matched_pref_count = len([m for m in matched_skills if not m["is_required"]])
    total_pref_count = len(pref_job_skills)

    # -------------------------------------------------------------
    # 7. Generate Deterministic Human-Readable Explanation
    # -------------------------------------------------------------
    explanation = _generate_explanation(
        overall_score=overall_score,
        matched_req=matched_req_count,
        total_req=total_req_count,
        exp_score=exp_score,
        exp_gap=exp_gap,
        cand_exp=cand_exp,
        job_min_exp=job_min_exp,
        missing_req=missing_required_skills,
        partial=partial_skills,
        edu_meets=edu_meets,
    )

    return JobMatchResult(
        overall_score=overall_score,
        required_skills_score=req_skills_score,
        preferred_skills_score=pref_skills_score,
        experience_score=exp_score,
        education_score=edu_score,
        matched_skills=matched_skills,
        partial_skills=partial_skills,
        missing_required_skills=missing_required_skills,
        missing_preferred_skills=missing_preferred_skills,
        experience_gap=exp_gap,
        experience_gap_text=exp_gap_text,
        education_compatibility=edu_compatibility,
        total_required_skills_count=total_req_count,
        matched_required_skills_count=matched_req_count,
        total_preferred_skills_count=total_pref_count,
        matched_preferred_skills_count=matched_pref_count,
        active_weights=normalized_weights,
        explanation=explanation,
    )


def _generate_explanation(
    overall_score: float,
    matched_req: int,
    total_req: int,
    exp_score: float,
    exp_gap: float,
    cand_exp: float,
    job_min_exp: float,
    missing_req: List[Dict[str, Any]],
    partial: List[Dict[str, Any]],
    edu_meets: bool,
) -> str:
    """Produces a factually grounded, deterministic text explanation."""
    if overall_score >= 85.0:
        tier_str = "Strong Match"
    elif overall_score >= 70.0:
        tier_str = "Good Match"
    elif overall_score >= 50.0:
        tier_str = "Moderate Match"
    else:
        tier_str = "Low Match"

    parts: List[str] = [f"{tier_str} ({overall_score:.1f}%):"]

    # Skill match summary
    if total_req > 0:
        parts.append(f"You meet {matched_req} of {total_req} required technical skills.")
    else:
        parts.append("No specific mandatory skills required for this posting.")

    # Experience note
    if exp_score >= 100.0:
        if job_min_exp > 0:
            parts.append(f"You meet the experience requirement ({cand_exp:.1f} yrs vs {job_min_exp:.1f} yrs required).")
        else:
            parts.append("No prior experience required.")
    else:
        parts.append(f"You have a {exp_gap:.1f}-year experience gap ({cand_exp:.1f} yrs vs {job_min_exp:.1f} yrs required).")

    # Missing skills callout
    if missing_req:
        missing_names = [m["name"] for m in missing_req[:3]]
        rem = len(missing_req) - len(missing_names)
        rem_str = f" and {rem} more" if rem > 0 else ""
        parts.append(f"Key missing skills: {', '.join(missing_names)}{rem_str}.")

    # Related partial match callout
    if partial:
        p_item = partial[0]
        parts.append(
            f"Your '{p_item['candidate_skill_name']}' provides partial credit for '{p_item['job_skill_name']}' ({int(p_item['similarity_weight'] * 100)}% transferable)."
        )

    return " ".join(parts)
