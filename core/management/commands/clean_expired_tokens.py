from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken
)


class Command(BaseCommand):
    help = 'Remove tokens expirados da blacklist e outstanding tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a limpeza sem deletar os registros'
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING(
            f'\n🧹 Limpando tokens expirados...\n'
            f'Data de referência: {now.strftime("%d/%m/%Y %H:%M:%S")}\n'
        ))

        # Tokens expirados na blacklist
        expired_blacklisted = BlacklistedToken.objects.filter(
            token__expires_at__lt=now
        )
        blacklist_count = expired_blacklisted.count()

        # Outstanding tokens expirados
        expired_outstanding = OutstandingToken.objects.filter(
            expires_at__lt=now
        )
        outstanding_count = expired_outstanding.count()

        # Sessões expiradas
        from core.models import UserSession
        expired_sessions = UserSession.objects.filter(expires_at__lt=now)
        sessions_count = expired_sessions.count()

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '🔍 [DRY RUN] Seriam removidos:\n'
                f'  - {blacklist_count} tokens da blacklist\n'
                f'  - {outstanding_count} outstanding tokens\n'
                f'  - {sessions_count} sessões expiradas\n'
            ))
        else:
            # Deletar tokens
            expired_blacklisted.delete()
            self.stdout.write(self.style.SUCCESS(
                f'✅ Removidos {blacklist_count} tokens da blacklist'
            ))

            expired_outstanding.delete()
            self.stdout.write(self.style.SUCCESS(
                f'✅ Removidos {outstanding_count} outstanding tokens'
            ))

            # Deletar sessões expiradas
            expired_sessions.delete()
            self.stdout.write(self.style.SUCCESS(
                f'✅ Removidas {sessions_count} sessões expiradas'
            ))

            total_removed = blacklist_count + outstanding_count + sessions_count
            self.stdout.write(self.style.SUCCESS(
                f'\n🎉 Total: {total_removed} registros removidos com sucesso!\n'
            ))
