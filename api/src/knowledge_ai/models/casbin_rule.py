"""Casbin policy storage ORM model (Alembic-managed)."""

from casbin_async_sqlalchemy_adapter import create_casbin_rule_model

from knowledge_ai.models.base import Base

CasbinRule = create_casbin_rule_model(Base)
