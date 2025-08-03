# Blitzepanda

## Configuration

Before running the scripts in this repository you must provide two environment
variables so the code can connect to the database and authenticate with the
language model API.

- `DB_CONNECTION_STRING` – SQLAlchemy connection string used to create the
  database engine.
- `API_KEY` – API key for accessing the model API.

Example of how to set them in a shell:

```bash
export DB_CONNECTION_STRING="mysql+pymysql://user:password@localhost:3306/dianping"
export API_KEY="sk-<your-api-key>"
```
