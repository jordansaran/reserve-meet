"""
Funções utilitárias para o app core
"""
import re
from user_agents import parse


def get_client_ip(request):
    """
    Extrai o endereço IP real do cliente da requisição

    Considera proxies e headers comuns usados por load balancers
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_user_agent(user_agent_string):
    """
    Analisa o User-Agent e retorna informações amigáveis sobre o dispositivo

    Args:
        user_agent_string: String do User-Agent

    Returns:
        dict com informações do dispositivo: {
            'device_name': 'Chrome no Windows',
            'browser': 'Chrome',
            'browser_version': '120.0',
            'os': 'Windows',
            'os_version': '10',
            'device_type': 'PC' ou 'Mobile' ou 'Tablet'
        }
    """
    user_agent = parse(user_agent_string)

    # Nome do navegador
    browser = user_agent.browser.family
    browser_version = user_agent.browser.version_string

    # Sistema operacional
    os_name = user_agent.os.family
    os_version = user_agent.os.version_string

    # Tipo de dispositivo
    if user_agent.is_mobile:
        device_type = 'Mobile'
    elif user_agent.is_tablet:
        device_type = 'Tablet'
    elif user_agent.is_pc:
        device_type = 'PC'
    else:
        device_type = 'Unknown'

    # Nome amigável do dispositivo
    device_name = f"{browser} no {os_name}"
    if device_type in ['Mobile', 'Tablet']:
        device_name = f"{browser} no {os_name} ({device_type})"

    return {
        'device_name': device_name,
        'browser': browser,
        'browser_version': browser_version,
        'os': os_name,
        'os_version': os_version,
        'device_type': device_type,
    }


def get_device_info(request):
    """
    Extrai informações completas do dispositivo e IP da requisição

    Args:
        request: Django request object

    Returns:
        dict com todas as informações necessárias para UserSession
    """
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)

    device_info = parse_user_agent(user_agent_string)

    return {
        'ip_address': ip_address,
        'user_agent': user_agent_string,
        'device_name': device_info['device_name'],
        'browser': device_info['browser'],
        'browser_version': device_info['browser_version'],
        'os': device_info['os'],
        'os_version': device_info['os_version'],
        'device_type': device_info['device_type'],
    }


def get_location_from_ip(ip_address):
    """
    Obtém localização aproximada a partir do IP (cidade, país)

    Nota: Para produção, considere usar serviços como:
    - https://ipapi.co/ (gratuito até 1000 req/dia)
    - https://ip-api.com/ (gratuito com rate limit)
    - MaxMind GeoIP2 (banco de dados local)

    Args:
        ip_address: Endereço IP

    Returns:
        str: Localização no formato "Cidade, País" ou "Unknown"
    """
    # Implementação básica - retorna Unknown
    # Em produção, você deve implementar com um serviço de geolocalização
    if not ip_address or ip_address in ['127.0.0.1', 'localhost']:
        return 'Local'

    # TODO: Implementar chamada para API de geolocalização
    # Exemplo com ipapi.co (requer requests):
    # try:
    #     response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=2)
    #     if response.status_code == 200:
    #         data = response.json()
    #         city = data.get('city', '')
    #         country = data.get('country_name', '')
    #         return f"{city}, {country}" if city and country else country
    # except Exception:
    #     pass

    return 'Unknown'


def send_login_notification_email(user, device_info, ip_address, location):
    """
    Envia email de notificação de novo login para o usuário

    Args:
        user: Instância do usuário
        device_info: Dict com informações do dispositivo
        ip_address: Endereço IP do login
        location: Localização aproximada
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils import timezone

    subject = f'Novo login detectado na sua conta - {settings.SITE_URL_API}'

    message = f"""
    Olá {user.first_name or user.username},

    Detectamos um novo login na sua conta:

    📱 Dispositivo: {device_info.get('device_name', 'Unknown')}
    🌐 Navegador: {device_info.get('browser', 'Unknown')} {device_info.get('browser_version', '')}
    💻 Sistema: {device_info.get('os', 'Unknown')} {device_info.get('os_version', '')}
    🌍 IP: {ip_address}
    📍 Localização: {location}
    ⏰ Data/Hora: {timezone.now().strftime('%d/%m/%Y às %H:%M:%S')}

    Se este login não foi feito por você, recomendamos que você:
    1. Altere sua senha imediatamente
    2. Faça logout de todos os dispositivos
    3. Entre em contato com o suporte

    Você pode gerenciar suas sessões ativas em: {settings.SITE_URL_API}/api/users/sessions/

    ---
    Esta é uma mensagem automática, por favor não responda.
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    except Exception as e:
        # Log do erro mas não interrompe o fluxo
        print(f"Erro ao enviar email de notificação: {e}")
