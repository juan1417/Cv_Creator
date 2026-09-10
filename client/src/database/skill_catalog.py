from uuid import UUID
from sqlmodel import Session, select, col
from .DB import get_engine
from models.skill_catalog import SkillCatalog

# ── Seed data: common tech skills ────────────────────────────────────────

SEED_SKILLS: list[tuple[str, str]] = [
    # Programming Languages
    ("Python", "Lenguajes"),
    ("JavaScript", "Lenguajes"),
    ("TypeScript", "Lenguajes"),
    ("Java", "Lenguajes"),
    ("C#", "Lenguajes"),
    ("C++", "Lenguajes"),
    ("Go", "Lenguajes"),
    ("Rust", "Lenguajes"),
    ("PHP", "Lenguajes"),
    ("Ruby", "Lenguajes"),
    ("Swift", "Lenguajes"),
    ("Kotlin", "Lenguajes"),
    ("R", "Lenguajes"),
    ("Scala", "Lenguajes"),
    ("Perl", "Lenguajes"),
    ("Dart", "Lenguajes"),
    ("Lua", "Lenguajes"),
    ("Elixir", "Lenguajes"),
    ("Haskell", "Lenguajes"),
    ("SQL", "Lenguajes"),

    # Frontend
    ("React", "Frontend"),
    ("Next.js", "Frontend"),
    ("Vue.js", "Frontend"),
    ("Angular", "Frontend"),
    ("Svelte", "Frontend"),
    ("HTML", "Frontend"),
    ("CSS", "Frontend"),
    ("Tailwind CSS", "Frontend"),
    ("Bootstrap", "Frontend"),
    ("Material UI", "Frontend"),
    ("SASS/SCSS", "Frontend"),
    ("Redux", "Frontend"),
    ("Zustand", "Frontend"),
    ("Astro", "Frontend"),

    # Backend
    ("Node.js", "Backend"),
    ("Express.js", "Backend"),
    ("FastAPI", "Backend"),
    ("Django", "Backend"),
    ("Flask", "Backend"),
    ("Spring Boot", "Backend"),
    ("NestJS", "Backend"),
    ("ASP.NET", "Backend"),
    ("Rails", "Backend"),
    ("Laravel", "Backend"),
    ("Gin", "Backend"),
    ("Actix", "Backend"),

    # Databases
    ("PostgreSQL", "Bases de Datos"),
    ("MySQL", "Bases de Datos"),
    ("MongoDB", "Bases de Datos"),
    ("Redis", "Bases de Datos"),
    ("SQLite", "Bases de Datos"),
    ("Elasticsearch", "Bases de Datos"),
    ("DynamoDB", "Bases de Datos"),
    ("Cassandra", "Bases de Datos"),
    ("Supabase", "Bases de Datos"),
    ("Firebase", "Bases de Datos"),
    ("Neon", "Bases de Datos"),

    # DevOps & Cloud
    ("Docker", "DevOps y Cloud"),
    ("Kubernetes", "DevOps y Cloud"),
    ("AWS", "DevOps y Cloud"),
    ("Azure", "DevOps y Cloud"),
    ("GCP", "DevOps y Cloud"),
    ("Vercel", "DevOps y Cloud"),
    ("Netlify", "DevOps y Cloud"),
    ("CI/CD", "DevOps y Cloud"),
    ("GitHub Actions", "DevOps y Cloud"),
    ("Terraform", "DevOps y Cloud"),
    ("Nginx", "DevOps y Cloud"),

    # Tools & Others
    ("Git", "Herramientas"),
    ("GitHub", "Herramientas"),
    ("GitLab", "Herramientas"),
    ("Jira", "Herramientas"),
    ("Figma", "Herramientas"),
    ("Notion", "Herramientas"),
    ("Slack", "Herramientas"),
    ("VS Code", "Herramientas"),
    ("Postman", "Herramientas"),
    ("Jest", "Herramientas"),
    ("Cypress", "Herramientas"),
    ("Playwright", "Herramientas"),
    ("Pytest", "Herramientas"),

    # Data & AI
    ("Pandas", "Datos e IA"),
    ("NumPy", "Datos e IA"),
    ("TensorFlow", "Datos e IA"),
    ("PyTorch", "Datos e IA"),
    ("Scikit-learn", "Datos e IA"),
    ("OpenCV", "Datos e IA"),
    ("LangChain", "Datos e IA"),
    ("LLMs", "Datos e IA"),
    ("Machine Learning", "Datos e IA"),
    ("Data Analysis", "Datos e IA"),
    ("Power BI", "Datos e IA"),
    ("Tableau", "Datos e IA"),

    # Soft Skills
    ("Liderazgo", "Soft Skills"),
    ("Comunicación", "Soft Skills"),
    ("Trabajo en Equipo", "Soft Skills"),
    ("Resolución de Problemas", "Soft Skills"),
    ("Pensamiento Crítico", "Soft Skills"),
    ("Gestión del Tiempo", "Soft Skills"),
    ("Adaptabilidad", "Soft Skills"),
    ("Creatividad", "Soft Skills"),
    ("Inglés", "Idiomas"),
    ("Portugués", "Idiomas"),
    ("Francés", "Idiomas"),
    ("Alemán", "Idiomas"),
    ("Chino", "Idiomas"),
    ("Japonés", "Idiomas"),
]


def seed_skills() -> int:
    """Insert predefined skills into the catalog. Returns count inserted. Idempotent."""
    engine = get_engine()
    inserted = 0
    with Session(engine) as session:
        existing = {
            row[0]
            for row in session.exec(select(SkillCatalog.name)).all()
        }
        for name, category in SEED_SKILLS:
            if name not in existing:
                session.add(SkillCatalog(name=name, category=category))
                inserted += 1
        if inserted:
            try:
                session.commit()
            except Exception:
                session.rollback()
                # Another instance already seeded — ignore
                inserted = 0
    return inserted


def search_skills(query: str, limit: int = 20) -> list[dict]:
    """Search skills by name (case-insensitive partial match)."""
    engine = get_engine()
    with Session(engine) as session:
        stmt = (
            select(SkillCatalog)
            .where(col(SkillCatalog.name).ilike(f"%{query}%"))
            .order_by(SkillCatalog.name)
            .limit(limit)
        )
        results = session.exec(stmt).all()
        return [
            {"id": str(s.id), "name": s.name, "category": s.category, "is_custom": s.is_custom}
            for s in results
        ]


def list_skills_by_category() -> dict[str, list[dict]]:
    """List all skills grouped by category."""
    engine = get_engine()
    with Session(engine) as session:
        results = session.exec(
            select(SkillCatalog).order_by(SkillCatalog.category, SkillCatalog.name)
        ).all()
        grouped: dict[str, list[dict]] = {}
        for s in results:
            grouped.setdefault(s.category, []).append(
                {"id": str(s.id), "name": s.name, "is_custom": s.is_custom}
            )
        return grouped


def add_custom_skill(name: str, category: str = "Custom", user_id: UUID | None = None) -> dict | None:
    """Add a user-defined skill to the catalog."""
    engine = get_engine()
    with Session(engine) as session:
        existing = session.exec(
            select(SkillCatalog).where(col(SkillCatalog.name).ilike(name))
        ).first()
        if existing:
            return {"id": str(existing.id), "name": existing.name, "category": existing.category, "is_custom": existing.is_custom}

        skill = SkillCatalog(name=name, category=category, is_custom=True, idUser=user_id)
        session.add(skill)
        session.commit()
        session.refresh(skill)
        return {"id": str(skill.id), "name": skill.name, "category": skill.category, "is_custom": skill.is_custom}
