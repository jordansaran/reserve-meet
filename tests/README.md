# Guia de Testes - Reserve Meet

Este documento descreve a estrutura de testes do projeto e como executá-los.

## Estrutura de Testes

```
tests/
├── __init__.py           # Pacote de testes
├── conftest.py           # Fixtures compartilhadas (pytest)
├── factories.py          # Factories para criação de dados de teste
├── test_models.py        # Testes unitários dos modelos
├── test_serializers.py   # Testes unitários dos serializers
├── test_validators.py    # Testes unitários dos validadores
└── test_api.py          # Testes de integração da API
```

## Tecnologias Utilizadas

- **pytest** - Framework de testes
- **pytest-django** - Plugin pytest para Django
- **factory-boy** - Criação de fixtures/dados de teste
- **faker** - Geração de dados fake realistas
- **pytest-cov** - Cobertura de código

## Tipos de Testes

### Testes Unitários (Unit Tests)

Testam componentes individuais isoladamente:

- **test_models.py** - Testa models, métodos, validações e relacionamentos
- **test_serializers.py** - Testa serialização/deserialização de dados
- **test_validators.py** - Testa validadores customizados (CEP, Estado)

### Testes de Integração (Integration Tests)

Testam a integração entre componentes e comportamento da API:

- **test_api.py** - Testa endpoints, autenticação, permissões e fluxos completos

## Executando os Testes

### Com Docker (Recomendado)

```bash
# Executar todos os testes
make test

# Executar com relatório de cobertura
make coverage

# Executar diretamente com docker-compose
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Ver relatório de cobertura
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Localmente (sem Docker)

```bash
# Instalar dependências de teste
make install-test

# Executar todos os testes
pytest

# Executar com verbose
pytest -v

# Executar com cobertura
pytest --cov=. --cov-report=html --cov-report=term-missing
```

## Executando Testes Específicos

### Por arquivo
```bash
# Testes de modelos
pytest tests/test_models.py

# Testes de API
pytest tests/test_api.py
```

### Por classe
```bash
# Testes do modelo User
pytest tests/test_models.py::TestUserModel

# Testes da API de Booking
pytest tests/test_api.py::TestBookingAPI
```

### Por método
```bash
# Teste específico
pytest tests/test_models.py::TestUserModel::test_create_user
```

### Por marker
```bash
# Apenas testes unitários
pytest -m unit

# Apenas testes de integração
pytest -m integration

# Excluir testes lentos
pytest -m "not slow"
```

## Factories Disponíveis

O arquivo `factories.py` contém factories para criação fácil de objetos de teste:

### Usuários
- `UserFactory` - Usuário comum
- `AdminUserFactory` - Usuário administrador
- `ManagerUserFactory` - Usuário gerente

### Booking
- `LocationFactory` - Localização/Prédio
- `ResourceFactory` - Recurso (Projetor, etc)
- `RoomFactory` - Sala de reunião
- `BookingFactory` - Reserva pendente
- `ConfirmedBookingFactory` - Reserva confirmada
- `CancelledBookingFactory` - Reserva cancelada
- `CompletedBookingFactory` - Reserva concluída

### Exemplo de uso

```python
from tests.factories import UserFactory, RoomFactory, BookingFactory

# Criar objetos individuais
user = UserFactory(email='test@example.com')
room = RoomFactory(capacity=20)

# Criar em lote
users = UserFactory.create_batch(10)

# Criar com relacionamentos
booking = BookingFactory(manager=user, room=room)
```

## Fixtures Disponíveis

O arquivo `conftest.py` contém fixtures reutilizáveis:

### Clientes API
- `api_client` - Cliente não autenticado
- `authenticated_client` - Cliente autenticado (usuário comum)
- `admin_client` - Cliente autenticado (admin)
- `manager_client` - Cliente autenticado (gerente)

### Usuários
- `user` - Usuário comum
- `admin_user` - Usuário administrador
- `manager_user` - Usuário gerente

### Objetos de Domínio
- `location` - Localização única
- `multiple_locations` - Lista de localizações
- `resource` - Recurso único
- `multiple_resources` - Lista de recursos
- `room` - Sala única
- `room_with_resources` - Sala com recursos
- `multiple_rooms` - Lista de salas
- `booking` - Reserva pendente
- `confirmed_booking` - Reserva confirmada
- `cancelled_booking` - Reserva cancelada
- `multiple_bookings` - Lista de reservas

### Exemplo de uso

```python
@pytest.mark.django_db
def test_criar_reserva(authenticated_client, user, room):
    """Testa criação de reserva"""
    data = {
        'manager': user.id,
        'room': room.id,
        'date_booking': '2025-12-01',
        # ...
    }
    response = authenticated_client.post('/api/bookings/', data)
    assert response.status_code == 201
```

## Cobertura de Código

O projeto utiliza `pytest-cov` para medir a cobertura de código.

### Gerar relatório
```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

### Ver relatório HTML
```bash
open htmlcov/index.html
```

### Áreas excluídas da cobertura
- Migrations (`*/migrations/*`)
- Arquivos de teste (`*/test_*.py`)
- Configurações (`*/settings/*`)
- Cache (`*/__pycache__/*`)
- WSGI/ASGI

## Configuração do Banco de Dados

Os testes utilizam um banco PostgreSQL isolado configurado no `docker-compose.test.yml`:

- **Nome do DB**: `meet_test`
- **Usuário**: `postgres`
- **Senha**: `postgres`
- **Armazenamento**: tmpfs (em memória, mais rápido)

O banco é criado e destruído automaticamente a cada execução.

### Reuso do Banco (mais rápido)

O pytest está configurado com `--reuse-db` para reutilizar o banco entre execuções:

```bash
# Primeira execução cria o banco
pytest

# Execuções seguintes reutilizam
pytest  # Mais rápido!

# Recriar banco se necessário
pytest --create-db
```

## Boas Práticas

### 1. Usar Markers
```python
@pytest.mark.django_db  # Necessário para testes com banco
@pytest.mark.unit       # Marca como teste unitário
def test_algo():
    pass
```

### 2. Usar Fixtures
```python
def test_com_fixtures(authenticated_client, user, room):
    # Fixtures injetadas automaticamente
    pass
```

### 3. Usar Factories
```python
# Bom: Usar factories
user = UserFactory()

# Evitar: Criar manualmente
user = User.objects.create(email='...', username='...')
```

### 4. Nomes Descritivos
```python
# Bom
def test_user_cannot_delete_other_user_booking():
    pass

# Evitar
def test_booking():
    pass
```

### 5. Arrange-Act-Assert
```python
def test_confirm_booking(manager_client, booking):
    # Arrange (preparar)
    url = reverse('booking-confirm', kwargs={'pk': booking.pk})

    # Act (executar)
    response = manager_client.post(url)

    # Assert (verificar)
    assert response.status_code == 200
    assert response.data['status'] == 'confirmed'
```

## Troubleshooting

### Erro: "no such table"
```bash
# Recriar o banco de dados de teste
pytest --create-db
```

### Erro: "permission denied"
```bash
# Verificar permissões do Docker
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up --build
```

### Testes lentos
```bash
# Usar tmpfs para banco mais rápido (já configurado)
# Ou pular testes lentos
pytest -m "not slow"
```

### Limpar cache
```bash
# Limpar cache do pytest
pytest --cache-clear

# Limpar tudo
make clean
```

## CI/CD

Para integração contínua, adicione ao seu pipeline:

```yaml
# Exemplo GitHub Actions
- name: Run tests
  run: |
    docker-compose -f docker-compose.test.yml up --abort-on-container-exit
    docker-compose -f docker-compose.test.yml down -v
```

## Referências

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [factory-boy](https://factoryboy.readthedocs.io/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)
