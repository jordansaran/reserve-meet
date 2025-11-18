FROM python:3.13.9-alpine as base

RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PATH="/root/.local/bin:/home/appuser/.local/bin:$PATH" \
    LANG=pt_BR.UTF-8 \
    LC_ALL=pt_BR.UTF-8

RUN apk add --no-cache \
    postgresql-client \
    libpq \
    poppler-utils \
    wget \
    procps \
    curl \
    musl-locales \
    musl-locales-lang

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    postgresql-dev \
    pkgconf \
    build-base

RUN echo "export LANG=pt_BR.UTF-8" > /etc/profile.d/locale.sh && \
    echo "export LC_ALL=pt_BR.UTF-8" >> /etc/profile.d/locale.sh

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    uv --version

WORKDIR /app

COPY pyproject.toml ./
COPY settings/ ./settings/
RUN uv pip install --system -e .

RUN apk del .build-deps

RUN chown -R appuser:appuser /app

USER appuser

FROM base as development
USER root

RUN apk add --no-cache --virtual .build-deps \
    build-base postgresql-dev pkgconf && \
    uv pip install --system -e ".[dev]" && \
    apk del .build-deps && \
    chown -R appuser:appuser /app

RUN cat > /entrypoint.sh << 'EOF'
#!/bin/sh
set -e

echo "🔍 Aguardando PostgreSQL..."
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-postgres}

while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER > /dev/null 2>&1; do
  sleep 1
done
echo "✅ PostgreSQL disponível!"

echo "🔄 Rodando migrations..."
python manage.py migrate --noinput

if [ "$DJANGO_SETTINGS_MODULE" = "settings.settings" ]; then

  echo "👤 Verificando superuser..."
  python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superuser criado: admin/admin123')
else:
    print('ℹ️  Superuser já existe')
END
fi

echo "🚀 Iniciando aplicação..."
exec "$@"
EOF

RUN chmod +x /entrypoint.sh && \
    chown appuser:appuser /entrypoint.sh && \
    chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
