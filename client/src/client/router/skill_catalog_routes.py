from uuid import UUID
from fastapi import APIRouter, Query

from database.skill_catalog import search_skills, list_skills_by_category, add_custom_skill

router = APIRouter(prefix="/api/skills-catalog", tags=["skills-catalog"])


@router.get("/search")
def api_search_skills(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=50)):
    return {"results": search_skills(q, limit)}


@router.get("/by-category")
def api_list_by_category():
    return {"categories": list_skills_by_category()}


@router.post("/custom")
def api_add_custom_skill(name: str = Query(..., min_length=1), category: str = Query("Custom")):
    skill = add_custom_skill(name, category)
    return {"skill": skill}
