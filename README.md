# Multi_Agent_KD

This project implements a multi-agent system using LangChain and a Neo4j knowledge graph for autonomous Non-Destructive Testing (NDT) planning.

## Configuration

### Ollama LLM Model
The application uses Ollama to serve local Large Language Models. You can specify which Ollama model the agents should use by setting the `OLLAMA_MODEL` environment variable. If not set, it defaults to `"mistral"`.

Example:
```bash
export OLLAMA_MODEL="llama2"
streamlit run app/main.py
```

Refer to the Ollama documentation for available models.

### Neo4j Connection
Ensure your Neo4j instance is running and accessible. Connection parameters are configured via the following environment variables:
- `NEO4J_URI`: The URI for your Neo4j instance (e.g., `bolt://localhost:7687`)
- `NEO4J_USER`: The username for Neo4j (e.g., `neo4j`)
- `NEO4J_PASSWORD`: The password for Neo4j.

These are typically set in a `.env` file that is loaded by the application.