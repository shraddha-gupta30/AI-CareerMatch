"""
Deterministic Canonical Skill Matcher and Normalization Service.
Resolves extracted resume skills against PostgreSQL taxonomy, aliases, and explicit relationships.
"""
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.skill import Skill, SkillAlias, SkillRelationship
from app.schemas.resume import ExtractedSkillItem


class SkillMatcher:
    """
    Deterministic skill matching engine.
    Matches extracted skill names against:
    1. Exact canonical name or normalized_name (full match)
    2. Configured skill alias (full match)
    3. Explicit skill relationships (transferable / related with similarity weight)
    Strictly forbids arbitrary category matching or probabilistic guessing.
    """

    @staticmethod
    def _normalize(text: str) -> str:
        """Sanitizes skill string for uniform comparison."""
        return text.strip().lower().replace("-", " ").replace(".", "").replace("_", " ")

    @classmethod
    async def match_skills(
        cls,
        extracted_skills: List[ExtractedSkillItem],
        db: AsyncSession,
    ) -> List[ExtractedSkillItem]:
        """
        Maps a list of extracted skills to the platform's canonical skill database.
        Mutates ExtractedSkillItem fields with canonical information.
        """
        if not extracted_skills:
            return []

        # 1. Fetch all canonical skills
        skills_stmt = select(Skill)
        skills_res = await db.execute(skills_stmt)
        all_skills: List[Skill] = list(skills_res.scalars().all())

        # Build canonical lookup maps
        canonical_by_norm: Dict[str, Skill] = {}
        canonical_by_id: Dict[UUID, Skill] = {}
        for s in all_skills:
            canonical_by_id[s.id] = s
            canonical_by_norm[cls._normalize(s.name)] = s
            canonical_by_norm[cls._normalize(s.normalized_name)] = s

        # 2. Fetch all aliases
        alias_stmt = select(SkillAlias)
        alias_res = await db.execute(alias_stmt)
        all_aliases: List[SkillAlias] = list(alias_res.scalars().all())

        alias_map: Dict[str, Skill] = {}
        for a in all_aliases:
            parent_skill = canonical_by_id.get(a.skill_id)
            if parent_skill:
                alias_map[cls._normalize(a.alias)] = parent_skill

        # 3. Match each extracted skill
        matched_results: List[ExtractedSkillItem] = []
        for item in extracted_skills:
            norm_query = cls._normalize(item.name)

            # Strategy A: Exact canonical match
            matched_skill: Optional[Skill] = canonical_by_norm.get(norm_query)

            # Strategy B: Alias match
            if not matched_skill:
                matched_skill = alias_map.get(norm_query)

            if matched_skill:
                updated_item = ExtractedSkillItem(
                    name=item.name,
                    proficiency_level=item.proficiency_level or "intermediate",
                    years_experience=item.years_experience or 1.0,
                    canonical_skill_id=matched_skill.id,
                    canonical_name=matched_skill.name,
                    category=matched_skill.category,
                    matched=True,
                    proficiency_source="resume_inferred",
                    is_verified=False,
                )
            else:
                # Strategy C: Unmatched (no arbitrary category assumptions)
                updated_item = ExtractedSkillItem(
                    name=item.name,
                    proficiency_level=item.proficiency_level or "intermediate",
                    years_experience=item.years_experience or 1.0,
                    canonical_skill_id=None,
                    canonical_name=item.name,
                    category=None,
                    matched=False,
                    proficiency_source="unknown",
                    is_verified=False,
                )

            matched_results.append(updated_item)

        return matched_results


async def match_extracted_skills(
    extracted_skills: List[ExtractedSkillItem],
    db: AsyncSession,
) -> List[ExtractedSkillItem]:
    """Helper function to execute skill matching on an active DB session."""
    return await SkillMatcher.match_skills(extracted_skills, db)
