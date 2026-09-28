```json
{"issues": [
  {"id": "I1", "depends_on": ["I2"], "touches": ["src/"]},
  {"id": "I2", "depends_on": ["I1", "I9"], "touches": ["src/api/*.ts"]}
]}
```
