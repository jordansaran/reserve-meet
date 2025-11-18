.PHONY: help install install-dev install-test build up down restart logs shell migrate makemigrations createsuperuser test coverage clean

help:
	@echo "📋 Comandos disponíveis:"
	@echo ""
	@echo "🔧 Instalação:"
	@echo "  make install       - Instala dependências de produção"
	@echo "  make install-dev   - Instala dependências de desenvolvimento"
	@echo "  make install-test  - Instala dependências de teste"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make build         - Build das imagens Docker"
	@echo "  make up            - Sobe ambiente de desenvolvimento"
	@echo "  make down          - Derruba ambiente"
	@echo "  make restart       - Reinicia containers"
	@echo "  make logs          - Mostra logs do Django"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  make migrate       - Roda migrations"
	@echo "  make makemigrations- Cria migrations"
	@echo "  make shell         - Acessa Django shell"
	@echo "  make createsuperuser - Cria superuser"
	@echo ""
	@echo "🧪 Testes:"
	@echo "  make test          - Roda testes"
	@echo "  make coverage      - Roda testes com coverage"
	@echo ""
	@echo "🧹 Limpeza:"
	@echo "  make clean         - Remove cache e arquivos temporários"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

install-test:
	uv pip install -e ".[test]"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "✅ Ambiente disponível em http://localhost:8000"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f web

shell:
	docker-compose exec web python manage.py shell

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

test:
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit
	docker-compose -f docker-compose.test.yml down

coverage:
	docker-compose -f docker-compose.test.yml run --rm test pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "✅ Coverage report: htmlcov/index.html"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/
	@echo "✅ Cache limpo!"