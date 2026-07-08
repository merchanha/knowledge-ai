#!/usr/bin/env bash
# Smoke-test Weeks 10–11 REST endpoints against a running local server.
#
# Usage (pick one):
#   TOKEN="eyJ..." ./scripts/smoke-test.sh
#   ./scripts/smoke-test.sh "eyJ..."
#   export TOKEN="eyJ..."; ./scripts/smoke-test.sh
#
# Optional env:
#   BASE_URL=http://localhost:8000   (default)
#   KEEP=1                           skip cleanup (leave project/data in DB)
#
# Prerequisites:
#   - docker compose up -d && uv run alembic upgrade head
#   - uvicorn running on port 8000
#   - Valid JWT for a user with role=admin (see api/docs/04-rbac-with-casbin.md)

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API="${BASE_URL}/api/v1"
TOKEN="${TOKEN:-${1:-}}"
KEEP="${KEEP:-0}"
STAMP="$(date +%s)"

if [[ -z "${TOKEN}" ]]; then
  echo "Error: JWT access token required."
  echo ""
  echo "Get a token:"
  echo "  1. Open: ${BASE_URL}/api/v1/auth/google/login?redirect_uri=http://localhost:5173/auth/callback"
  echo "  2. Complete Google login"
  echo "  3. Copy the value after #token= in the redirect URL"
  echo ""
  echo "Then run:"
  echo "  TOKEN=\"<paste-token>\" ./scripts/smoke-test.sh"
  echo "  ./scripts/smoke-test.sh \"<paste-token>\""
  exit 1
fi

for cmd in curl jq; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Error: '${cmd}' is required. Install it and retry."
    exit 1
  fi
done

AUTH=(-H "Authorization: Bearer ${TOKEN}")
JSON=(-H "Content-Type: application/json")

step() {
  echo ""
  echo "==> $1"
}

pass() {
  echo "    OK: $1"
}

fail() {
  echo "    FAIL: $1" >&2
  exit 1
}

# $1=label $2=expected_http $3=actual_http $4=optional body snippet
assert_status() {
  local label=$1 expected=$2 actual=$3
  if [[ "${actual}" != "${expected}" ]]; then
    echo "    Response body: ${4:-}" >&2
    fail "${label} (HTTP ${actual}, expected ${expected})"
  fi
  pass "${label}"
}

# --- Health (no auth) ---
step "Health checks"
code=$(curl -s -o /tmp/smoke-health.json -w "%{http_code}" "${API}/health")
assert_status "GET /health" 200 "${code}"
jq -e '.status == "ok"' /tmp/smoke-health.json >/dev/null || fail "/health body"

code=$(curl -s -o /tmp/smoke-ready.json -w "%{http_code}" "${API}/health/ready")
assert_status "GET /health/ready" 200 "${code}"
jq -e '
  .status == "ok"
  and ([.dependencies[] | select(.name == "database" and .status == "ok")] | length) == 1
  and ([.dependencies[] | select(.name == "redis" and .status == "ok")] | length) == 1
' /tmp/smoke-ready.json >/dev/null \
  || fail "/health/ready — is docker compose up? ($(cat /tmp/smoke-ready.json))"

# --- Auth ---
step "Authenticated profile"
code=$(curl -s -o /tmp/smoke-me.json -w "%{http_code}" "${AUTH[@]}" "${API}/auth/me")
assert_status "GET /auth/me" 200 "${code}"
USER_ID=$(jq -r '.id' /tmp/smoke-me.json)
USER_ROLE=$(jq -r '.role' /tmp/smoke-me.json)
USER_EMAIL=$(jq -r '.email' /tmp/smoke-me.json)
echo "    user: ${USER_EMAIL} (${USER_ID}), role=${USER_ROLE}"

if [[ "${USER_ROLE}" != "admin" ]]; then
  echo ""
  echo "Warning: role is '${USER_ROLE}', not 'admin'. Project create will fail."
  echo "Promote yourself, re-login, and rerun:"
  echo "  UPDATE users SET role = 'admin' WHERE email = '${USER_EMAIL}';"
  exit 1
fi

# --- Week 11: Project ---
step "Create project (admin)"
PROJECT_NAME="SmokeTest-${STAMP}"
code=$(curl -s -o /tmp/smoke-project.json -w "%{http_code}" \
  -X POST "${AUTH[@]}" "${JSON[@]}" \
  -d "{\"name\": \"${PROJECT_NAME}\", \"description\": \"smoke-test script\"}" \
  "${API}/projects")
assert_status "POST /projects" 201 "${code}" "$(cat /tmp/smoke-project.json)"
PROJECT_ID=$(jq -r '.id' /tmp/smoke-project.json)
echo "    project_id: ${PROJECT_ID}"

step "List projects"
code=$(curl -s -o /tmp/smoke-projects.json -w "%{http_code}" "${AUTH[@]}" "${API}/projects")
assert_status "GET /projects" 200 "${code}"
jq -e --arg id "${PROJECT_ID}" '.[] | select(.id == $id)' /tmp/smoke-projects.json >/dev/null \
  || fail "created project not in list"

step "Get project tree (find Root)"
code=$(curl -s -o /tmp/smoke-tree.json -w "%{http_code}" \
  "${AUTH[@]}" "${API}/projects/${PROJECT_ID}/directories/tree")
assert_status "GET /projects/{id}/directories/tree" 200 "${code}"
ROOT_ID=$(jq -r '.[] | select(.is_root == true) | .id' /tmp/smoke-tree.json | head -n1)
[[ -n "${ROOT_ID}" && "${ROOT_ID}" != "null" ]] || fail "root directory not found"
echo "    root_id: ${ROOT_ID}"

step "Create Scripts subdirectory"
FOLDER_NAME="SmokeScripts-${STAMP}"
code=$(curl -s -o /tmp/smoke-folder.json -w "%{http_code}" \
  -X POST "${AUTH[@]}" "${JSON[@]}" \
  -d "{\"name\": \"${FOLDER_NAME}\"}" \
  "${API}/directories/${ROOT_ID}/children")
assert_status "POST /directories/{id}/children" 201 "${code}"
DIRECTORY_ID=$(jq -r '.id' /tmp/smoke-folder.json)
echo "    directory_id: ${DIRECTORY_ID}"

step "Add self as project owner (membership + Casbin MANAGE on root)"
code=$(curl -s -o /tmp/smoke-member.json -w "%{http_code}" \
  -X POST "${AUTH[@]}" "${JSON[@]}" \
  -d "{\"user_id\": \"${USER_ID}\", \"role\": \"owner\"}" \
  "${API}/projects/${PROJECT_ID}/members")
# 201 first time; 409 if re-run without cleanup
if [[ "${code}" == "201" ]]; then
  pass "POST /projects/{id}/members"
elif [[ "${code}" == "409" ]]; then
  pass "POST /projects/{id}/members (already a member)"
else
  fail "POST /projects/{id}/members (HTTP ${code})"
fi

step "Account: list projects + toggle is_context_exposed"
code=$(curl -s -o /tmp/smoke-account.json -w "%{http_code}" "${AUTH[@]}" "${API}/account")
assert_status "GET /account" 200 "${code}"

code=$(curl -s -o /tmp/smoke-exposure.json -w "%{http_code}" \
  -X PATCH "${AUTH[@]}" "${JSON[@]}" \
  -d '{"is_context_exposed": true}' \
  "${API}/account/projects/${PROJECT_ID}")
assert_status "PATCH /account/projects/{id}" 200 "${code}"
jq -e '.is_context_exposed == true' /tmp/smoke-exposure.json >/dev/null || fail "exposure toggle"

step "Admin: list users"
code=$(curl -s -o /tmp/smoke-users.json -w "%{http_code}" "${AUTH[@]}" "${API}/admin/users")
assert_status "GET /admin/users" 200 "${code}"
jq -e --arg id "${USER_ID}" '.[] | select(.id == $id)' /tmp/smoke-users.json >/dev/null \
  || fail "current user not in admin user list"

# --- Week 10: Commands ---
step "Create command"
code=$(curl -s -o /tmp/smoke-command.json -w "%{http_code}" \
  -X POST "${AUTH[@]}" "${JSON[@]}" \
  -d '{"title": "Run Tests", "content": "uv run pytest", "metadata": {"tags": ["smoke"]}}' \
  "${API}/directories/${DIRECTORY_ID}/commands")
assert_status "POST /directories/{id}/commands" 201 "${code}"
COMMAND_ID=$(jq -r '.id' /tmp/smoke-command.json)
echo "    command_id: ${COMMAND_ID}"

step "List commands in directory"
code=$(curl -s -o /tmp/smoke-commands.json -w "%{http_code}" \
  "${AUTH[@]}" "${API}/directories/${DIRECTORY_ID}/commands")
assert_status "GET /directories/{id}/commands" 200 "${code}"
jq -e --arg id "${COMMAND_ID}" '.[] | select(.id == $id)' /tmp/smoke-commands.json >/dev/null \
  || fail "command not in list"

step "Get command"
code=$(curl -s -o /tmp/smoke-command-get.json -w "%{http_code}" \
  "${AUTH[@]}" "${API}/commands/${COMMAND_ID}")
assert_status "GET /commands/{id}" 200 "${code}"

step "Update command"
code=$(curl -s -o /tmp/smoke-command-patch.json -w "%{http_code}" \
  -X PATCH "${AUTH[@]}" "${JSON[@]}" \
  -d '{"title": "Run Full Suite"}' \
  "${API}/commands/${COMMAND_ID}")
assert_status "PATCH /commands/{id}" 200 "${code}"
jq -e '.title == "Run Full Suite"' /tmp/smoke-command-patch.json >/dev/null || fail "command title"

step "Delete command"
code=$(curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE "${AUTH[@]}" "${API}/commands/${COMMAND_ID}")
assert_status "DELETE /commands/{id}" 204 "${code}"

# --- Cleanup ---
if [[ "${KEEP}" != "1" ]]; then
  step "Cleanup: delete smoke project"
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    -X DELETE "${AUTH[@]}" "${API}/projects/${PROJECT_ID}")
  assert_status "DELETE /projects/{id}" 204 "${code}"
else
  echo ""
  echo "KEEP=1 set — left project ${PROJECT_ID} in database."
fi

echo ""
echo "All smoke checks passed."
