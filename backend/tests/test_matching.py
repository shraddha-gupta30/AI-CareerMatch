"""
Unit Tests for Pure Deterministic Matching Engine.
Covers exact matching, aliases, explicit skill_relationships partial credit,
proficiency ranks, confidence weighting, experience gap, education compatibility,
N/A proportional weight redistribution, and deterministic repeatability.
"""
from types import SimpleNamespace
import pytest
from app.services.matching_engine import (
    calculate_job_match,
    JobMatchResult,
)


def _make_candidate(
    skills=None,
    total_experience_years=3.0,
    education_degree="Bachelor of Science in Computer Science",
):
    """Helper to build candidate object."""
    skills_list = []
    for s in (skills or []):
        if isinstance(s, str):
            skills_list.append(SimpleNamespace(name=s, proficiency_level="intermediate", proficiency_source="user_verified"))
        elif isinstance(s, dict):
            skills_list.append(SimpleNamespace(
                name=s.get("name", ""),
                proficiency_level=s.get("proficiency_level", "intermediate"),
                proficiency_source=s.get("proficiency_source", "user_verified"),
            ))
        else:
            skills_list.append(s)

    edu_records = []
    if education_degree:
        edu_records.append(SimpleNamespace(degree=education_degree))

    return SimpleNamespace(
        skills=skills_list,
        total_experience_years=total_experience_years,
        education=edu_records,
    )


def _make_job(
    required_skills=None,
    preferred_skills=None,
    min_experience_years=2.0,
    target_education_level="Bachelor",
):
    """Helper to build job object."""
    job_skills = []
    for s in (required_skills or []):
        if isinstance(s, str):
            job_skills.append(SimpleNamespace(
                name=s,
                is_required=True,
                importance_weight=1.0,
                min_proficiency="intermediate",
            ))
        elif isinstance(s, dict):
            job_skills.append(SimpleNamespace(
                name=s.get("name", ""),
                is_required=True,
                importance_weight=s.get("importance_weight", 1.0),
                min_proficiency=s.get("min_proficiency", "intermediate"),
            ))

    for s in (preferred_skills or []):
        if isinstance(s, str):
            job_skills.append(SimpleNamespace(
                name=s,
                is_required=False,
                importance_weight=1.0,
                min_proficiency="intermediate",
            ))
        elif isinstance(s, dict):
            job_skills.append(SimpleNamespace(
                name=s.get("name", ""),
                is_required=False,
                importance_weight=s.get("importance_weight", 1.0),
                min_proficiency=s.get("min_proficiency", "intermediate"),
            ))

    return SimpleNamespace(
        job_skills=job_skills,
        min_experience_years=min_experience_years,
        target_education_level=target_education_level,
    )


def test_exact_skill_match():
    """1. Exact skill match produces 1.0 full credit."""
    cand = _make_candidate(skills=["Python", "FastAPI"])
    job = _make_job(required_skills=["Python", "FastAPI"])
    result = calculate_job_match(cand, job)

    assert result.required_skills_score == 100.0
    assert result.matched_required_skills_count == 2
    assert len(result.missing_required_skills) == 0


def test_alias_match():
    """2. Alias resolution maps synonyms to canonical skills."""
    cand = _make_candidate(skills=["ReactJS", "NodeJS"])
    job = _make_job(required_skills=["React", "Node.js"])
    aliases = {
        "reactjs": "React",
        "nodejs": "Node.js",
    }
    result = calculate_job_match(cand, job, skill_alias_map=aliases)

    assert result.required_skills_score == 100.0
    assert result.matched_required_skills_count == 2


def test_explicit_related_skill_partial_match():
    """3. Explicit skill_relationships provides proportional partial credit."""
    # Candidate has MySQL; Job requires PostgreSQL
    cand = _make_candidate(skills=["MySQL"])
    job = _make_job(required_skills=["PostgreSQL"])
    rel_map = {
        "MySQL": {"PostgreSQL": 0.7}
    }
    result = calculate_job_match(cand, job, relationships_map=rel_map)

    assert len(result.partial_skills) == 1
    assert result.partial_skills[0]["candidate_skill_name"] == "MySQL"
    assert result.partial_skills[0]["similarity_weight"] == 0.7
    assert result.required_skills_score == 70.0


def test_missing_required_skill():
    """4. Missing required skill yields 0 credit for that skill."""
    cand = _make_candidate(skills=["Python"])
    job = _make_job(required_skills=["Python", "Docker"])
    result = calculate_job_match(cand, job)

    # 1 matched, 1 missing -> 50%
    assert result.required_skills_score == 50.0
    assert len(result.missing_required_skills) == 1
    assert result.missing_required_skills[0]["name"] == "Docker"


def test_missing_preferred_skill():
    """5. Missing preferred skill affects preferred score but not required score."""
    cand = _make_candidate(skills=["Python"])
    job = _make_job(required_skills=["Python"], preferred_skills=["Kubernetes"])
    result = calculate_job_match(cand, job)

    assert result.required_skills_score == 100.0
    assert result.preferred_skills_score == 0.0
    assert len(result.missing_preferred_skills) == 1


def test_proficiency_scaling():
    """6. Candidate with lower proficiency receives proportional proficiency penalty."""
    cand_beg = _make_candidate(skills=[{"name": "Python", "proficiency_level": "beginner"}])
    cand_adv = _make_candidate(skills=[{"name": "Python", "proficiency_level": "advanced"}])
    job = _make_job(required_skills=[{"name": "Python", "min_proficiency": "intermediate"}])

    res_beg = calculate_job_match(cand_beg, job)
    res_adv = calculate_job_match(cand_adv, job)

    # Beginner (1) / Intermediate (2) = 0.5 -> 50.0%
    assert res_beg.required_skills_score == 50.0
    # Advanced (3) >= Intermediate (2) = 1.0 -> 100.0%
    assert res_adv.required_skills_score == 100.0


def test_confidence_weighting():
    """7. user_verified gives 1.0 confidence while resume_inferred gives 0.9 confidence."""
    cand_ver = _make_candidate(skills=[{"name": "Python", "proficiency_level": "intermediate", "proficiency_source": "user_verified"}])
    cand_inf = _make_candidate(skills=[{"name": "Python", "proficiency_level": "intermediate", "proficiency_source": "resume_inferred"}])
    job = _make_job(required_skills=[{"name": "Python", "min_proficiency": "intermediate"}])

    res_ver = calculate_job_match(cand_ver, job)
    res_inf = calculate_job_match(cand_inf, job)

    assert res_ver.required_skills_score == 100.0
    assert res_inf.required_skills_score == 90.0


def test_experience_compatibility():
    """8. Experience compatibility computes bounded score and accurate gap."""
    job = _make_job(required_skills=["Python"], min_experience_years=4.0)

    # Candidate with 2.0 years (50% experience)
    cand_under = _make_candidate(skills=["Python"], total_experience_years=2.0)
    res_under = calculate_job_match(cand_under, job)
    assert res_under.experience_score == 50.0
    assert res_under.experience_gap == 2.0
    assert "2.0 years below requirement" in res_under.experience_gap_text

    # Candidate with 5.0 years (100% experience)
    cand_over = _make_candidate(skills=["Python"], total_experience_years=5.0)
    res_over = calculate_job_match(cand_over, job)
    assert res_over.experience_score == 100.0
    assert res_over.experience_gap == 0.0


def test_education_compatibility():
    """9. Education hierarchy evaluates degree compatibility."""
    job_bs = _make_job(required_skills=["Python"], target_education_level="Bachelor")

    cand_bs = _make_candidate(skills=["Python"], education_degree="B.S. in Computer Science")
    res_bs = calculate_job_match(cand_bs, job_bs)
    assert res_bs.education_score == 100.0
    assert res_bs.education_compatibility["meets_requirement"] is True

    cand_assoc = _make_candidate(skills=["Python"], education_degree="Associate Degree in IT")
    res_assoc = calculate_job_match(cand_assoc, job_bs)
    assert res_assoc.education_score == 75.0
    assert res_assoc.education_compatibility["meets_requirement"] is False

    # BTech correctly recognized as Bachelor level (100.0% match)
    cand_btech = _make_candidate(skills=["Python"], education_degree="BTech in Computer Science")
    res_btech = calculate_job_match(cand_btech, job_bs)
    assert res_btech.education_score == 100.0
    assert res_btech.education_compatibility["candidate_highest_level"] == "Bachelor"
    assert res_btech.education_compatibility["meets_requirement"] is True

    # Master's degree (MTech) meets or exceeds Bachelor requirement
    cand_mtech = _make_candidate(skills=["Python"], education_degree="MTech in Artificial Intelligence")
    res_mtech = calculate_job_match(cand_mtech, job_bs)
    assert res_mtech.education_score == 100.0
    assert res_mtech.education_compatibility["candidate_highest_level"] == "Master"
    assert res_mtech.education_compatibility["meets_requirement"] is True


def test_na_weight_redistribution():
    """10. When a dimension is N/A (e.g. no preferred skills), weights proportionally redistribute to sum to 1.0."""
    # Job has NO preferred skills
    job_no_pref = _make_job(
        required_skills=["Python"],
        preferred_skills=[],
        min_experience_years=2.0,
        target_education_level="Bachelor",
    )
    cand = _make_candidate(skills=["Python"], total_experience_years=2.0, education_degree="B.S. in CS")
    result = calculate_job_match(cand, job_no_pref)

    # Active dimensions should be required_skills, experience, education
    assert "preferred_skills" not in result.active_weights
    assert result.preferred_skills_score is None

    # Base weights: 0.50 + 0.20 + 0.10 = 0.80
    # Normalized: 0.50/0.80 = 0.625, 0.20/0.80 = 0.25, 0.10/0.80 = 0.125
    assert sum(result.active_weights.values()) == pytest.approx(1.0, abs=1e-3)
    assert result.active_weights["required_skills"] == pytest.approx(0.625, abs=1e-3)
    assert result.overall_score == 100.0


def test_deterministic_repeatability():
    """11. CRITICAL: Calling calculate_job_match twice with identical inputs yields bit-for-bit identical results."""
    cand = _make_candidate(
        skills=[
            {"name": "Python", "proficiency_level": "advanced", "proficiency_source": "user_verified"},
            {"name": "MySQL", "proficiency_level": "intermediate", "proficiency_source": "resume_inferred"},
        ],
        total_experience_years=2.5,
        education_degree="Bachelor of Engineering",
    )
    job = _make_job(
        required_skills=["Python", "PostgreSQL"],
        preferred_skills=["Docker"],
        min_experience_years=3.0,
        target_education_level="Bachelor",
    )
    rel_map = {"MySQL": {"PostgreSQL": 0.7}}

    run_1 = calculate_job_match(cand, job, relationships_map=rel_map)
    run_2 = calculate_job_match(cand, job, relationships_map=rel_map)

    assert run_1.overall_score == run_2.overall_score
    assert run_1.required_skills_score == run_2.required_skills_score
    assert run_1.preferred_skills_score == run_2.preferred_skills_score
    assert run_1.experience_score == run_2.experience_score
    assert run_1.education_score == run_2.education_score
    assert run_1.explanation == run_2.explanation
    assert run_1.to_dict() == run_2.to_dict()


def test_score_boundedness():
    """12. Scores are strictly bounded in [0.0, 100.0] under any edge inputs."""
    # Empty candidate
    cand_empty = _make_candidate(skills=[], total_experience_years=0.0, education_degree=None)
    job_demanding = _make_job(required_skills=["C++", "Rust"], min_experience_years=10.0, target_education_level="Doctorate")

    res_zero = calculate_job_match(cand_empty, job_demanding)
    assert 0.0 <= res_zero.overall_score <= 100.0
    assert res_zero.required_skills_score == 0.0

    # Overqualified candidate
    cand_expert = _make_candidate(
        skills=[{"name": "C++", "proficiency_level": "expert"}],
        total_experience_years=20.0,
        education_degree="Ph.D. in Computer Science",
    )
    job_junior = _make_job(required_skills=["C++"], min_experience_years=1.0, target_education_level="Associate")
    res_high = calculate_job_match(cand_expert, job_junior)
    assert 0.0 <= res_high.overall_score <= 100.0
    assert res_high.overall_score == 100.0


def test_gemini_independence():
    """13. The matching engine computes numeric scores without calling external Gemini services."""
    cand = _make_candidate(skills=["Java"])
    job = _make_job(required_skills=["Java"])
    res = calculate_job_match(cand, job)
    assert isinstance(res, JobMatchResult)
    assert res.overall_score == 100.0
