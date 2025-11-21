from django.contrib import admin
from booking.models import (
    Resource,
    Booking,
    Location,
    Room
)
from django.utils.translation import gettext_lazy as _


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'is_active']
    list_filter = ['is_active', 'state', 'city']
    search_fields = ['name', 'address', 'city']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'capacity', 'is_active']
    list_filter = ['is_active', 'location']
    search_fields = ['name']
    filter_horizontal = ['resources']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'room',
        'manager',
        'date_booking',
        'start_datetime',
        'end_datetime',
        'status',
        'has_coffee_break',
        'is_active'
    ]
    list_filter = [
        'status',
        'is_active',
        'has_coffee_break',
        'date_booking',
        'room__location'
    ]
    search_fields = [
        'room__name',
        'manager__email',
        'manager__username',
        'notes'
    ]
    readonly_fields = [
        'confirmed_by',
        'confirmed_at',
        'cancelled_by',
        'cancelled_at',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        (_('Informações Básicas'), {
            'fields': (
                'manager',
                'room',
                'date_booking',
                'start_datetime',
                'end_datetime',
                'is_active'
            )
        }),
        (_('Coffee Break'), {
            'fields': (
                'has_coffee_break',
                'coffee_break_headcount'
            )
        }),
        (_('Status e Confirmação'), {
            'fields': (
                'status',
                'confirmed_by',
                'confirmed_at',
                'cancelled_by',
                'cancelled_at',
                'cancellation_reason'
            )
        }),
        (_('Observações'), {
            'fields': ('notes',)
        }),
        (_('Datas do Sistema'), {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    actions = ['confirm_bookings', 'cancel_bookings']

    def confirm_bookings(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='confirmed',
            confirmed_by=request.user,
            confirmed_at=timezone.now()
        )
        self.message_user(request, f'{updated} reservas confirmadas com sucesso.')

    confirm_bookings.short_description = _('Confirmar reservas selecionadas')

    def cancel_bookings(self, request, queryset):
        from django.utils import timezone
        updated = queryset.exclude(status='cancelled').update(
            status='cancelled',
            cancelled_by=request.user,
            cancelled_at=timezone.now()
        )
        self.message_user(request, f'{updated} reservas canceladas.')

    cancel_bookings.short_description = _('Cancelar reservas selecionadas')
