# Reserve Meet

Sistema de gerenciamento de reservas de salas de reunião desenvolvido com Django REST Framework.

## Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [API Endpoints](#api-endpoints)
- [Testes](#testes)
- [Comandos Make](#comandos-make)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

## Sobre o Projeto

O **Reserve Meet** é uma API REST completa para gerenciamento de reservas de salas de reunião. O sistema permite:

- Gerenciar múltiplas localizações
- Cadastrar salas com capacidade e recursos específicos
- Realizar reservas com prevenção automática de conflitos de horário
- Controlar status de reservas (pendente, confirmado, cancelado, concluído)
- Gerenciar coffee breaks para reuniões
- Autenticação JWT com controle de permissões por roles

### Controle de Acesso por Roles

O sistema implementa três níveis de usuários:
- **User**: Usuários comuns que realizam reservas de salas
- **Manager**: Gerentes que cadastram localizações, recursos e salas, e visualizam todas as reservas
- **Admin**: Administradores com controle total do sistema

## Funcionalidades

### Gestão de Usuários e Autenticação
- **Registro público de usuários** com role "user" (endpoint público)
- **Sistema de autenticação JWT** (access e refresh tokens)
- **Controle de permissões** baseado em roles (user, manager, admin)
- **Perfis de usuário** com informações de contato completas
- **Gerenciamento de perfil**: visualizar e atualizar dados pessoais
- **Alteração de senha** com validação da senha atual

### Tipos de Usuários e Permissões

O sistema possui três tipos de usuários com diferentes níveis de acesso:

#### 🔵 User (Usuário Comum)
- **Função**: Realizar reservas de salas
- **Permissões**:
  - ✅ Criar, visualizar e gerenciar suas próprias reservas
  - ✅ **Listar e visualizar** todas as salas disponíveis (somente leitura)
  - ✅ **Listar e visualizar** todas as localizações (somente leitura)
  - ✅ **Listar e visualizar** todos os recursos disponíveis (somente leitura)
  - ✅ Gerenciar seu próprio perfil
  - ✅ Gerenciar suas sessões ativas
  - ❌ Não pode criar/editar/deletar salas, localizações ou recursos
  - ❌ Não pode ver reservas de outros usuários

#### 🟢 Manager (Gerente)
- **Função**: Administrar o sistema de salas e visualizar reservas
- **Permissões**:
  - ✅ Todas as permissões de User
  - ✅ Cadastrar e gerenciar localizações (prédios)
  - ✅ Cadastrar e gerenciar salas
  - ✅ Cadastrar e gerenciar recursos (projetor, ar-condicionado, etc.)
  - ✅ Visualizar lista completa de reservas de todas as salas
  - ✅ Confirmar e cancelar reservas
  - ❌ Não tem acesso ao painel administrativo Django
  - ❌ Não pode gerenciar usuários

#### 🔴 Admin (Administrador)
- **Função**: Controle total do sistema
- **Permissões**:
  - ✅ Todas as permissões de Manager
  - ✅ Acesso completo ao painel administrativo Django (`/admin/`)
  - ✅ Gerenciar todos os usuários (criar, editar, desativar)
  - ✅ Visualizar e gerenciar todas as sessões de usuários
  - ✅ Revogar sessões de qualquer usuário
  - ✅ Acesso a logs e auditoria completa do sistema
  - ✅ Configurações avançadas do sistema

**Nota**: Usuários criados via endpoint público (`POST /api/users/register/`) sempre recebem a role "user". Para criar managers ou admins, é necessário usar o painel administrativo Django.

### Autenticação Avançada e Segurança
- **Logout com blacklist de tokens**: invalidação server-side de tokens JWT
- **Logout de todos os dispositivos**: revogação em massa de sessões
- **Rastreamento de sessões por dispositivo**:
  - Captura de IP, user-agent, dispositivo e localização
  - Visualização de todas as sessões ativas
  - Revogação individual de sessões específicas
- **Notificações por email** em novos logins
- **Limpeza automática** de tokens e sessões expirados via management command
- **Proteção contra AnonymousUser** na geração do schema Swagger/OpenAPI

### Gestão de Localizações
- Cadastro de múltiplas localizações (prédios)
- Endereços completos com validação de CEP e estado brasileiro
- Descrições detalhadas das localizações

### Gestão de Salas
- Cadastro de salas por localização
- Definição de capacidade
- Associação de recursos (projetor, ar-condicionado, etc.)
- Validação de nomes únicos por localização

### Sistema de Reservas
- Criação de reservas com data e horário
- **Prevenção automática de conflitos de horário** usando PostgreSQL exclusion constraints
- Status de reserva: pendente, confirmado, cancelado, concluído
- Opção de coffee break com quantidade de pessoas
- Auditoria completa: quem confirmou/cancelou e quando
- Notas e motivos de cancelamento
- Índices otimizados para queries frequentes

### Recursos Adicionais
- Soft delete (registros mantêm histórico)
- Documentação automática da API com Swagger/OpenAPI
- Filtros, busca e ordenação em endpoints
- Paginação configurável
- CORS habilitado para integração com frontends

## Tecnologias

### Backend
- **Python 3.13**
- **Django 5.2.8** - Framework web
- **Django REST Framework 3.16** - API REST
- **Django REST Framework SimpleJWT 5.5** - Autenticação JWT com blacklist
- **PostgreSQL 15** - Banco de dados
- **drf-yasg 1.21** - Documentação Swagger/OpenAPI
- **user-agents 2.2+** - Parsing de User-Agent para detecção de dispositivos

### DevOps
- **Docker & Docker Compose** - Containerização
- **Gunicorn** - WSGI HTTP Server
- **uv** - Gerenciador de pacotes Python

### Desenvolvimento
- **pytest** - Framework de testes
- **factory-boy** - Geração de fixtures de teste
- **pytest-cov** - Cobertura de código
- **black** - Formatação de código
- **ruff** - Linting
- **isort** - Ordenação de imports

## Pré-requisitos

- Docker e Docker Compose instalados
- Make (opcional, mas recomendado)

**OU** para desenvolvimento local sem Docker:

- Python 3.13+
- PostgreSQL 15+
- uv (gerenciador de pacotes)

## Instalação

### Usando Docker (Recomendado)

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd reserve-meet
```

2. Copie o arquivo de ambiente (se houver):
```bash
cp .env.example .env  # Ajuste as variáveis conforme necessário
```

3. Build e inicie os containers:
```bash
make build
make up
```

4. Execute as migrations:
```bash
make migrate
```

5. Crie um superusuário:
```bash
make createsuperuser
```

A aplicação estará disponível em `http://localhost:8000`

### Instalação Local (sem Docker)

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd reserve-meet
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
make install-dev
```

4. Configure o banco de dados PostgreSQL e ajuste a variável `DATABASE_URL` no arquivo `.env`

5. Execute as migrations:
```bash
python manage.py migrate
```

6. Crie um superusuário:
```bash
python manage.py createsuperuser
```

7. Inicie o servidor:
```bash
python manage.py runserver
```

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/booking_dev

# JWT
JWT_ACCESS_TIME=15  # minutos
JWT_REFRESH_TIME=1  # dias

# Email (opcional - para notificações de login)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend  # desenvolvimento
# Para produção, use SMTP:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=seu-email@gmail.com
# EMAIL_HOST_PASSWORD=sua-senha-ou-app-password
# DEFAULT_FROM_EMAIL=noreply@reservemeet.com

# Static
STATIC_URL=/static/
STATIC_ROOT=staticfiles-api

# API
SITE_URL_API=http://localhost:8000
```

### PostgreSQL Extension

O projeto utiliza a extensão `btree_gist` do PostgreSQL para implementar exclusion constraints que previnem conflitos de reservas. Esta extensão é automaticamente criada via migration.

### Limpeza Automática de Tokens

Para manter o banco de dados limpo, recomenda-se agendar a execução periódica do comando de limpeza:

```bash
# No Docker
docker-compose exec web python manage.py clean_expired_tokens

# Local
python manage.py clean_expired_tokens
```

Este comando remove:
- Tokens da blacklist que já expiraram
- Outstanding tokens expirados
- Sessões de usuário expiradas

**Recomendação**: Agendar via cron ou task scheduler para executar diariamente.

## Uso

### Acessando a API

Após iniciar a aplicação, você pode acessar:

- **API Root**: `http://localhost:8000/api/`
- **Documentação Swagger**: `http://localhost:8000/swagger/`
- **Documentação ReDoc**: `http://localhost:8000/redoc/`
- **Admin Django**: `http://localhost:8000/admin/`

### Autenticação

A API utiliza JWT (JSON Web Tokens) para autenticação:

#### 1. Registrar novo usuário (público)
```bash
POST /api/users/register/
{
  "email": "usuario@example.com",
  "username": "usuario123",
  "password": "senha_segura",
  "password_confirm": "senha_segura",
  "first_name": "João",
  "last_name": "Silva"
}
```

#### 2. Obter tokens (login)
```bash
POST /api/token/
{
  "email": "usuario@example.com",
  "password": "senha_segura"
}
```

Retorna:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Nota**: Ao fazer login, uma sessão é automaticamente criada com informações do dispositivo, IP e localização. Um email de notificação é enviado (se configurado).

#### 3. Usar o token
Adicione o header em todas as requisições protegidas:
```
Authorization: Bearer <access_token>
```

#### 4. Renovar token
```bash
POST /api/token/refresh/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 5. Logout (invalidar token)
```bash
POST /api/logout/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 6. Logout de todos os dispositivos
```bash
POST /api/logout-all/
```

### Gerenciamento de Sessões

#### Listar todas as sessões do usuário
```bash
GET /api/users/sessions/
```

#### Listar apenas sessões ativas
```bash
GET /api/users/sessions/active/
```

#### Obter sessão atual
```bash
GET /api/users/sessions/current/
```

#### Revogar sessão específica
```bash
DELETE /api/users/sessions/{id}/revoke/
```

### Exemplo de Fluxo de Reserva

1. **Listar salas disponíveis**:
```bash
GET /api/booking/rooms/
```

2. **Criar uma reserva**:
```bash
POST /api/booking/bookings/
{
  "room": 1,
  "date_booking": "2025-11-25",
  "start_datetime": "2025-11-25T10:00:00",
  "end_datetime": "2025-11-25T12:00:00",
  "has_coffee_break": true,
  "coffee_break_headcount": 10,
  "notes": "Reunião de planejamento"
}
```

3. **Confirmar reserva** (requer permissões):
```bash
POST /api/booking/bookings/{id}/confirm/
```

4. **Cancelar reserva**:
```bash
POST /api/booking/bookings/{id}/cancel/
{
  "reason": "Reunião adiada"
}
```

## Estrutura do Projeto

```
reserve-meet/
├── booking/                  # App de reservas
│   ├── admin.py             # Configuração do admin
│   ├── choices.py           # Enums e choices
│   ├── models.py            # Modelos: Location, Room, Resource, Booking
│   ├── serializers.py       # Serializers DRF
│   ├── urls.py              # Rotas do app
│   ├── validators.py        # Validadores customizados
│   └── views.py             # ViewSets e views
├── core/                     # App core (usuários e autenticação)
│   ├── admin.py             # Configuração do admin (User, UserSession)
│   ├── choices.py           # Enums de roles
│   ├── managers.py          # Managers customizados (ActiveManager, UserManager)
│   ├── models.py            # BaseModel, User, UserSession
│   ├── serializers.py       # Serializers de usuário e sessões
│   ├── urls.py              # Rotas de autenticação e sessões
│   ├── utils.py             # Utilidades (captura de IP, device info, emails)
│   ├── views.py             # Views de usuário, login, logout e sessões
│   └── management/
│       └── commands/
│           └── clean_expired_tokens.py  # Limpeza de tokens expirados
├── settings/                 # Configurações Django
│   ├── settings.py          # Settings principais
│   ├── urls.py              # URLs principais
│   └── wsgi.py              # WSGI config
├── docker-compose.yml        # Configuração Docker desenvolvimento
├── docker-compose.test.yml   # Configuração Docker testes
├── Dockerfile                # Dockerfile multi-stage
├── Makefile                  # Comandos automatizados
├── manage.py                 # Django management
├── pyproject.toml            # Dependências e configurações
└── README.md                 # Este arquivo
```

## API Endpoints

### Autenticação (`/api/`)
- `POST /api/token/` - Obter access e refresh tokens (login)
- `POST /api/token/refresh/` - Renovar access token
- `POST /api/token/verify/` - Verificar validade do token
- `POST /api/logout/` - Logout (adiciona token à blacklist)
- `POST /api/logout-all/` - Logout de todos os dispositivos

### Usuários (`/api/users/`)
- `POST /api/users/register/` - **Registro público** de novo usuário (AllowAny)
- `GET /api/users/me/` - Perfil do usuário autenticado
- `PATCH /api/users/me/` - Atualizar perfil do usuário autenticado
- `POST /api/users/change-password/` - Alterar senha
- `GET /api/users/` - Listar usuários (admin only)
- `GET /api/users/{id}/` - Detalhes do usuário (admin only)
- `PUT /api/users/{id}/` - Atualizar usuário (admin only)
- `PATCH /api/users/{id}/` - Atualizar parcial (admin only)
- `DELETE /api/users/{id}/` - Desativar usuário (admin only)

### Sessões de Usuário (`/api/users/sessions/`)
- `GET /api/users/sessions/` - Listar todas as sessões do usuário
- `GET /api/users/sessions/active/` - Listar apenas sessões ativas
- `GET /api/users/sessions/current/` - Obter sessão atual
- `GET /api/users/sessions/{id}/` - Detalhes de uma sessão
- `DELETE /api/users/sessions/{id}/revoke/` - Revogar sessão específica

### Localizações (`/api/booking/locations/`)
- `GET /api/booking/locations/` - Listar localizações **(todos os usuários autenticados)**
- `GET /api/booking/locations/{id}/` - Detalhes **(todos os usuários autenticados)**
- `POST /api/booking/locations/` - Criar localização **(apenas admin)**
- `PUT/PATCH /api/booking/locations/{id}/` - Atualizar **(apenas admin)**
- `DELETE /api/booking/locations/{id}/` - Desativar **(apenas admin)**

### Salas (`/api/booking/rooms/`)
- `GET /api/booking/rooms/` - Listar salas **(todos os usuários autenticados)**
- `GET /api/booking/rooms/{id}/` - Detalhes da sala **(todos os usuários autenticados)**
- `POST /api/booking/rooms/` - Criar sala **(apenas admin)**
- `PUT/PATCH /api/booking/rooms/{id}/` - Atualizar **(apenas admin)**
- `DELETE /api/booking/rooms/{id}/` - Desativar **(apenas admin)**

### Recursos (`/api/booking/resources/`)
- `GET /api/booking/resources/` - Listar recursos **(todos os usuários autenticados)**
- `GET /api/booking/resources/{id}/` - Detalhes do recurso **(todos os usuários autenticados)**
- `POST /api/booking/resources/` - Criar recurso **(apenas admin)**
- `PUT/PATCH /api/booking/resources/{id}/` - Atualizar **(apenas admin)**
- `DELETE /api/booking/resources/{id}/` - Desativar **(apenas admin)**

### Reservas (`/api/booking/bookings/`)
- `GET /api/booking/bookings/` - Listar reservas
- `POST /api/booking/bookings/` - Criar reserva
- `GET /api/booking/bookings/{id}/` - Detalhes
- `PUT/PATCH /api/booking/bookings/{id}/` - Atualizar
- `DELETE /api/booking/bookings/{id}/` - Cancelar (soft delete)
- `POST /api/booking/bookings/{id}/confirm/` - Confirmar reserva
- `POST /api/booking/bookings/{id}/cancel/` - Cancelar com motivo
- `POST /api/booking/bookings/{id}/complete/` - Marcar como concluída

**Filtros disponíveis**: As listagens suportam filtros por campos relevantes, busca textual e ordenação.

## Testes

O projeto inclui uma suite completa de testes com **pytest** e **factory-boy**:

### Cobertura de Testes
- **72+ testes unitários** (models, serializers, validators)
- **31+ testes de integração** (API de usuários, logout)
- **19+ testes de integração** (API de sessões)
- **Cobertura total: 100+ testes**

### Comandos Básicos

#### Executar todos os testes
```bash
# Usando Make (recomendado)
make test

# Ou usando Docker Compose diretamente
docker-compose -f docker-compose.test.yml run --rm test
```

#### Executar com relatório de cobertura
```bash
# Usando Make
make coverage

# Ou manualmente
docker-compose -f docker-compose.test.yml run --rm test pytest --cov=. --cov-report=html --cov-report=term
```

O relatório HTML estará disponível em `htmlcov/index.html`

### Executar Testes Específicos

```bash
# Todos os testes de um arquivo
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_models.py

# Apenas uma classe de teste
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_user_api.py::TestUserRegistrationAPI

# Apenas um teste específico
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_user_api.py::TestUserRegistrationAPI::test_register_new_user

# Testes de API de usuários
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_user_api.py

# Testes de API de sessões
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_sessions_api.py
```

### Opções Úteis do pytest

```bash
# Modo verboso (mostra cada teste)
docker-compose -f docker-compose.test.yml run --rm test pytest -v

# Parar no primeiro erro
docker-compose -f docker-compose.test.yml run --rm test pytest -x

# Mostrar prints/outputs durante os testes
docker-compose -f docker-compose.test.yml run --rm test pytest -s

# Executar último teste que falhou
docker-compose -f docker-compose.test.yml run --rm test pytest --lf

# Executar testes que falharam + próximos
docker-compose -f docker-compose.test.yml run --rm test pytest --ff

# Executar em paralelo (mais rápido)
docker-compose -f docker-compose.test.yml run --rm test pytest -n auto

# Filtrar testes por nome
docker-compose -f docker-compose.test.yml run --rm test pytest -k "test_login"

# Mostrar duração dos 10 testes mais lentos
docker-compose -f docker-compose.test.yml run --rm test pytest --durations=10
```

### Markers Disponíveis
```bash
# Apenas testes unitários
docker-compose -f docker-compose.test.yml run --rm test pytest -m unit

# Apenas testes de integração
docker-compose -f docker-compose.test.yml run --rm test pytest -m integration

# Pular testes lentos
docker-compose -f docker-compose.test.yml run --rm test pytest -m "not slow"
```

### Ver Relatório de Cobertura

```bash
# Gerar relatório HTML de cobertura
docker-compose -f docker-compose.test.yml run --rm test pytest --cov=. --cov-report=html

# Abrir no navegador
open htmlcov/index.html        # Mac
xdg-open htmlcov/index.html    # Linux
start htmlcov/index.html       # Windows
```

### Executar Localmente (sem Docker)

```bash
# Ativar ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar dependências de teste
make install-test
# ou
uv pip install -e ".[test]"

# Executar testes
pytest
pytest -v                                    # Verboso
pytest tests/test_models.py                 # Arquivo específico
pytest -m unit                               # Por marcador
pytest --cov=. --cov-report=html            # Com cobertura
```

### Dicas Úteis

```bash
# Limpar cache do pytest
docker-compose -f docker-compose.test.yml run --rm test pytest --cache-clear

# Ver quais testes seriam executados (dry-run)
docker-compose -f docker-compose.test.yml run --rm test pytest --collect-only

# Combinar múltiplas opções
docker-compose -f docker-compose.test.yml run --rm test pytest -v -x -s tests/test_user_api.py
```

### Estrutura de Testes
```
tests/
├── conftest.py              # Fixtures compartilhadas (api_client, authenticated_client, etc.)
├── factories.py             # Factory-boy factories para todos os models
├── test_models.py           # Testes unitários de models
├── test_serializers.py      # Testes unitários de serializers
├── test_validators.py       # Testes de validadores customizados
├── test_user_api.py         # Testes de integração da API de usuários (30 testes)
└── test_sessions_api.py     # Testes de integração da API de sessões (10 testes)
```

### Fixtures Disponíveis

As seguintes fixtures estão disponíveis em `tests/conftest.py`:

- `api_client` - Cliente API não autenticado
- `authenticated_client` - Cliente API autenticado (usuário comum)
- `admin_client` - Cliente API autenticado (admin)
- `user` - Usuário comum de teste
- `admin_user` - Usuário admin de teste
- `location` - Localização de teste
- `room` - Sala de teste
- `booking` - Reserva de teste

Exemplo de uso:
```python
def test_my_endpoint(authenticated_client, user):
    response = authenticated_client.get('/api/users/me/')
    assert response.status_code == 200
    assert response.data['email'] == user.email
```

## Comandos Make

O projeto inclui um Makefile com comandos úteis:

### Instalação
- `make install` - Instala dependências de produção
- `make install-dev` - Instala dependências de desenvolvimento
- `make install-test` - Instala dependências de teste

### Docker
- `make build` - Build das imagens Docker
- `make up` - Sobe ambiente de desenvolvimento
- `make down` - Derruba ambiente
- `make restart` - Reinicia containers
- `make logs` - Mostra logs do Django

### Database
- `make migrate` - Executa migrations
- `make makemigrations` - Cria novas migrations
- `make shell` - Acessa Django shell
- `make createsuperuser` - Cria superusuário

### Comandos de Management
- `python manage.py clean_expired_tokens` - Limpa tokens e sessões expirados
- `python manage.py clean_expired_tokens --dry-run` - Simula limpeza sem deletar

### Testes
- `make test` - Executa testes
- `make coverage` - Executa testes com relatório de cobertura

### Limpeza
- `make clean` - Remove cache e arquivos temporários

Para ver todos os comandos disponíveis:
```bash
make help
```

## Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código

O projeto utiliza:
- **Black** para formatação
- **Ruff** para linting
- **isort** para ordenação de imports

Execute antes de commitar:
```bash
black .
ruff check .
isort .
```

### Commits

Siga o padrão de commits convencionais:
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação
- `refactor:` - Refatoração
- `test:` - Testes
- `chore:` - Manutenção

## Licença

Este projeto está sob a licença especificada no arquivo [LICENSE](LICENSE).

---

Desenvolvido com Django REST Framework
