"""Template service — CRUD and Jinja2 rendering. Uses str IDs (SQLite/PostgreSQL portable)."""
import json

from fastapi import HTTPException
from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import ConfigTemplate
from app.schemas.template import TemplateCreate, TemplateUpdate


def _render(template_content: str, variables: dict) -> str:
    """Render a Jinja2 template string with given variables."""
    env = Environment(undefined=StrictUndefined, autoescape=False)
    try:
        tmpl = env.from_string(template_content)
        return tmpl.render(**variables)
    except TemplateSyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Template syntax error: {e}")
    except UndefinedError as e:
        raise HTTPException(status_code=400, detail=f"Missing variable: {e}")


async def list_templates(db: AsyncSession, vendor: str | None = None) -> list[ConfigTemplate]:
    q = select(ConfigTemplate).order_by(ConfigTemplate.name)
    if vendor:
        q = q.where(ConfigTemplate.vendor == vendor)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_template_or_404(db: AsyncSession, template_id: str) -> ConfigTemplate:
    result = await db.execute(select(ConfigTemplate).where(ConfigTemplate.id == str(template_id)))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return tmpl


async def create_template(db: AsyncSession, data: TemplateCreate, created_by: str) -> ConfigTemplate:
    existing = await db.execute(select(ConfigTemplate).where(ConfigTemplate.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Template name already exists")
    # Validate template syntax immediately
    try:
        env = Environment(undefined=StrictUndefined, autoescape=False)
        env.parse(data.template_content)
    except TemplateSyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Template syntax error: {e}")

    schema_str = json.dumps(data.variables_schema) if isinstance(data.variables_schema, dict) else str(data.variables_schema)
    tmpl = ConfigTemplate(
        name=data.name,
        description=data.description,
        vendor=data.vendor,
        template_content=data.template_content,
        variables_schema=schema_str,
        created_by=str(created_by),
    )
    db.add(tmpl)
    await db.flush()
    return tmpl


async def update_template(db: AsyncSession, template_id: str, data: TemplateUpdate) -> ConfigTemplate:
    tmpl = await get_template_or_404(db, template_id)
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if field == "variables_schema" and isinstance(value, dict):
            value = json.dumps(value)
        setattr(tmpl, field, value)
    await db.flush()
    return tmpl


async def delete_template(db: AsyncSession, template_id: str) -> None:
    tmpl = await get_template_or_404(db, template_id)
    await db.delete(tmpl)
    await db.flush()


async def preview_template(
    db: AsyncSession, template_id: str, variables: dict, device_hostname: str | None = None
) -> dict:
    tmpl = await get_template_or_404(db, template_id)
    ctx = {"device": {"hostname": device_hostname or "preview-device"}, **variables}
    rendered = _render(tmpl.template_content, ctx)
    return {
        "rendered_config": rendered,
        "variables_used": ctx,
        "template_name": tmpl.name,
    }
