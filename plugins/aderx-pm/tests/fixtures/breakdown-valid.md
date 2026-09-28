## Issue graph
```json
{"feature": "x", "issues": [
  {"id": "I1", "title": "types", "depends_on": [], "touches": ["src/types/invite.ts", "db/migrations/"]},
  {"id": "I2", "title": "api", "depends_on": ["I1"], "touches": ["src/api/invites/"]},
  {"id": "I3", "title": "ui", "depends_on": ["I1"], "touches": ["web/pages/invite.tsx"]},
  {"id": "I4", "title": "e2e", "depends_on": ["I2", "I3"], "touches": ["e2e/invite.spec.ts"]}
]}
```
