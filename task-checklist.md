# Milestone 20: Role-Based Access Control (RBAC) - Task Checklist

## Phase 1: Fix Failing Password Reset Tests (Milestone 19 cleanup)
- [ ] Fix rate limiter unit tests (monkeypatching issues)
- [ ] Fix test_concurrent_forgot_password_requests (NameError: status)
- [ ] Fix test_password_saved_to_history (history not saved)
- [ ] Fix test_common_password_rejected (422 vs 400)
- [ ] Fix test_old_password_cannot_be_reused (password history)
- [ ] Fix test_successful_reset_requires_strong_password (password policy)
- [ ] Fix test_password_reset_with_weak_password (E2E flow)
- [ ] Run all backend tests (verify 224+ pass)

## Phase 2: RBAC Backend Implementation
- [ ] Create Role model (Role, UserRole tables)
- [ ] Create Permission model
- [ ] Create RBAC schemas
- [ ] Create RBAC service layer
- [ ] Create RBAC API endpoints
- [ ] Add RBAC dependencies (require_role, require_permission)
- [ ] Add Alembic migration for RBAC tables
- [ ] Seed default roles (admin, manager, user, viewer)

## Phase 3: RBAC Frontend Implementation
- [ ] Add RBAC API functions to frontend/lib/api.ts
- [ ] Create roles management page
- [ ] Create permissions management page
- [ ] Add role assignment UI to user management
- [ ] Update Navigation with RBAC links

## Phase 4: RBAC Integration
- [ ] Integrate RBAC checks into existing endpoints
- [ ] Add RBAC audit logging
- [ ] Write RBAC backend tests
- [ ] Write RBAC frontend tests

## Phase 5: Finalize
- [ ] Run all backend tests (verify all pass)
- [ ] Run frontend tests
- [ ] Update PROJECT_STATUS.md
- [ ] Update README.md