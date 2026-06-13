# ─────────────────────────────────────────────────────────────
# SMD GLOBAL CONSULTING LLC — Audit RGPD/IA
# Dockerfile — compatible Render.com (Free/Starter plan)
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Métadonnées
LABEL maintainer="SMD GLOBAL CONSULTING LLC <diallosouleymane19@gmail.com>"
LABEL description="Micro-Audits RGPD/IA Act pour TPE — API FastAPI"

# Variables d'environnement système
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Utilisateur non-root pour la sécurité
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# Port (Render.com injecte $PORT automatiquement)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Démarrage — Render.com passe PORT via $PORT
CMD uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 2 \
    --log-level info
