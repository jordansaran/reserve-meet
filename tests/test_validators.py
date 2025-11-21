"""
Testes unitários para validadores customizados
"""
import pytest
from django.core.exceptions import ValidationError

from booking.validators import cep_validator, validate_brazilian_state


@pytest.mark.unit
class TestCepValidator:
    """Testes para o validador de CEP"""

    def test_valid_cep(self):
        """Testa CEP válido"""
        valid_ceps = [
            '12345-678',
            '00000-000',
            '99999-999',
        ]
        for cep in valid_ceps:
            try:
                cep_validator(cep)
            except ValidationError:
                pytest.fail(f'CEP {cep} deveria ser válido')

    def test_invalid_cep_format(self):
        """Testa CEP com formato inválido"""
        invalid_ceps = [
            '12345678',      # Sem hífen
            '123456-78',     # Formato errado
            '12345-67',      # Poucos dígitos
            '123456-789',    # Muitos dígitos na primeira parte
            '12345-6789',    # Muitos dígitos na segunda parte
            '1234-678',      # Poucos dígitos na primeira parte
            'abcde-fgh',     # Letras
            '12.345-678',    # Ponto ao invés de hífen
            '',              # Vazio
            '12345 678',     # Espaço ao invés de hífen
        ]
        for cep in invalid_ceps:
            with pytest.raises(ValidationError):
                cep_validator(cep)


@pytest.mark.unit
class TestBrazilianStateValidator:
    """Testes para o validador de estado brasileiro"""

    def test_valid_states_uppercase(self):
        """Testa todos os estados válidos em maiúsculo"""
        valid_states = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
        for state in valid_states:
            try:
                validate_brazilian_state(state)
            except ValidationError:
                pytest.fail(f'Estado {state} deveria ser válido')

    def test_valid_states_lowercase(self):
        """Testa estados válidos em minúsculo (são convertidos)"""
        valid_states_lower = ['sp', 'rj', 'mg', 'rs', 'pr']
        for state in valid_states_lower:
            try:
                validate_brazilian_state(state)
            except ValidationError:
                pytest.fail(f'Estado {state} deveria ser válido')

    def test_invalid_states(self):
        """Testa estados inválidos"""
        invalid_states = [
            'XX',       # Código inexistente
            'ZZ',       # Código inexistente
            'BR',       # País, não estado
            'ABC',      # Mais de 2 caracteres
            'A',        # Apenas 1 caractere
            '12',       # Números
            'S',        # Incompleto
            '',         # Vazio
            'SP ',      # Com espaço
            ' SP',      # Com espaço
        ]
        for state in invalid_states:
            with pytest.raises(ValidationError):
                validate_brazilian_state(state)

    def test_state_validation_error_message(self):
        """Testa mensagem de erro do validador"""
        with pytest.raises(ValidationError) as exc_info:
            validate_brazilian_state('XX')

        error = exc_info.value
        assert 'XX' in str(error)
        assert error.code == 'invalid_state'

    def test_all_brazilian_states_count(self):
        """Testa que temos todos os 26 estados + DF"""
        valid_states = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
        assert len(valid_states) == 27  # 26 estados + DF
