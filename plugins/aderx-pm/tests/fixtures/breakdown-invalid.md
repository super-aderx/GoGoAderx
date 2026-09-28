```json
{"issues": [
  {"id": "I1", "wave": 0, "depends_on": ["I2"], "touches": ["src/"]},
  {"id": "I2", "wave": 0, "depends_on": ["I1", "I9"], "touches": ["src/api/*.ts"]}
]}
```
