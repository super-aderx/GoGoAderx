## Issue graph
```json
{"feature": "x", "issues": [
  {"id": "I1", "title": "types", "wave": 0, "depends_on": [], "touches": ["src/types/invite.ts", "db/migrations/"]},
  {"id": "I2", "title": "api", "wave": 1, "depends_on": ["I1"], "touches": ["src/api/invites/"]},
  {"id": "I3", "title": "ui", "wave": 1, "depends_on": ["I1"], "touches": ["web/pages/invite.tsx"]}
]}
```
