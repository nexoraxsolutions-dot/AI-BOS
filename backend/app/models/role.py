"""
Role-Based Access Control (RBAC) models.

Implements:
- Role: Named collection of permissions (admin, manager, user, viewer)
- Permission: Individual action-level authorization (users:read, users:write, etc.)
- UserRole: Many-to-many relationship between users and roles
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship

from app.db import Base


# Association table for role-permission many-to-many
role_permission_association = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    """Named collection of permissions."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    is_system_role = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    permissions = relationship(
        "Permission",
        secondary=role_permission_association,
        back_populates="roles",
        lazy="selectin",
    )
    user_roles = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )


class Permission(Base):
    """Individual action-level authorization."""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    resource = Column(String(50), nullable=False, index=True)  # e.g., 'users', 'companies', 'audit_logs'
    action = Column(String(50), nullable=False)  # e.g., 'read', 'write', 'delete', 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permission_association,
        back_populates="permissions",
        lazy="selectin",
    )


class UserRole(Base):
    """Many-to-many relationship between users and roles."""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles", lazy="selectin")
    assigner = relationship("User", foreign_keys=[assigned_by])