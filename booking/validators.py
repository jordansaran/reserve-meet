from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


cep_validator = RegexValidator(
    regex=r'^\d{5}-\d{3}$',
    message=_('CEP deve estar no formato: XXXXX-XXX (ex: 17607-140)'),
    code='invalid_cep'
)


def validate_brazilian_state(value):
    """
    Valida se o valor é uma sigla válida de estado brasileiro
    """
    BRAZILIAN_STATES = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]

    if value.upper() not in BRAZILIAN_STATES:
        raise ValidationError(
            _('%(value)s não é uma sigla válida de estado brasileiro. Use siglas como: SP, RJ, MG, etc.'),
            params={'value': value},
            code='invalid_state'
        )
