"""
Factories para criação de objetos de teste usando factory_boy
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from datetime import (
    datetime,
    timedelta
)
from django.utils import timezone
from core.models import User
from core.choices import UserRoles
from booking.models import (
    Location,
    Resource,
    Room,
    Booking
)
from booking.choices import BookingStatus


fake = Faker('pt_BR')


class UserFactory(DjangoModelFactory):
    """Factory para o modelo User"""

    class Meta:
        model = User
        django_get_or_create = ('email',)

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    phone = factory.LazyAttribute(lambda _: fake.phone_number())
    role = UserRoles.USER
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Define a senha após a criação do usuário"""
        if not create:
            return

        if extracted:
            obj.set_password(extracted) # type: ignore
        else:
            obj.set_password('testpass123') # type: ignore
        obj.save() # type: ignore


class AdminUserFactory(UserFactory):
    """Factory para usuário administrador"""

    email = factory.Sequence(lambda n: f'admin{n}@example.com')
    username = factory.Sequence(lambda n: f'admin{n}')
    role = UserRoles.ADMIN
    is_staff = True
    is_superuser = True


class ManagerUserFactory(UserFactory):
    """Factory para usuário gerente"""

    email = factory.Sequence(lambda n: f'manager{n}@example.com')
    username = factory.Sequence(lambda n: f'manager{n}')
    role = UserRoles.MANAGER
    is_staff = True


class LocationFactory(DjangoModelFactory):
    """Factory para o modelo Location"""

    class Meta:
        model = Location
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'Prédio {n}')
    address = factory.LazyAttribute(lambda _: fake.street_address())
    city = factory.LazyAttribute(lambda _: fake.city())
    state = factory.LazyAttribute(lambda _: fake.random_element(elements=[
        'SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'PE', 'CE', 'GO'
    ]))
    cep = factory.LazyAttribute(lambda _: f'{fake.random_int(10000, 99999)}-{fake.random_int(100, 999)}')
    description = factory.LazyAttribute(lambda obj: f'Localização do {obj.name}')
    is_active = True


class ResourceFactory(DjangoModelFactory):
    """Factory para o modelo Resource"""

    class Meta:
        model = Resource
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'Recurso {n}')
    description = factory.LazyAttribute(lambda obj: f'Descrição do {obj.name}')
    is_active = True


class RoomFactory(DjangoModelFactory):
    """Factory para o modelo Room"""

    class Meta:
        model = Room

    name = factory.Sequence(lambda n: f'Sala {n}')
    location = factory.SubFactory(LocationFactory)
    capacity = factory.LazyAttribute(lambda _: fake.random_int(min=5, max=50))
    is_active = True

    @factory.post_generation
    def resources(obj, create, extracted, **kwargs):
        """Adiciona recursos à sala após criação"""
        if not create:
            return

        if extracted:
            for resource in extracted:
                obj.resources.add(resource)


class BookingFactory(DjangoModelFactory):
    """Factory para o modelo Booking"""

    class Meta:
        model = Booking

    manager = factory.SubFactory(UserFactory)
    room = factory.SubFactory(RoomFactory)
    date_booking = factory.LazyAttribute(
        lambda _: (timezone.now() + timedelta(days=fake.random_int(1, 30))).date()
    )
    start_datetime = factory.LazyAttribute(
        lambda obj: timezone.make_aware(
            datetime.combine(obj.date_booking, datetime.min.time().replace(hour=9))
        )
    )
    end_datetime = factory.LazyAttribute(
        lambda obj: obj.start_datetime + timedelta(hours=2)
    )
    has_coffee_break = False
    coffee_break_headcount = 1
    status = BookingStatus.PENDING
    notes = factory.LazyAttribute(lambda _: fake.text(max_nb_chars=200))
    is_active = True


class ConfirmedBookingFactory(BookingFactory):
    """Factory para reserva confirmada"""

    status = BookingStatus.CONFIRMED
    confirmed_by = factory.SubFactory(ManagerUserFactory)
    confirmed_at = factory.LazyAttribute(lambda _: timezone.now())


class CancelledBookingFactory(BookingFactory):
    """Factory para reserva cancelada"""

    status = BookingStatus.CANCELLED
    cancelled_by = factory.SubFactory(UserFactory)
    cancelled_at = factory.LazyAttribute(lambda _: timezone.now())
    cancellation_reason = factory.LazyAttribute(lambda _: fake.sentence())


class CompletedBookingFactory(BookingFactory):
    """Factory para reserva concluída"""

    status = BookingStatus.COMPLETED
    date_booking = factory.LazyAttribute(
        lambda _: (timezone.now() - timedelta(days=fake.random_int(1, 30))).date()
    )
    start_datetime = factory.LazyAttribute(
        lambda obj: timezone.make_aware(
            datetime.combine(obj.date_booking, datetime.min.time().replace(hour=9))
        )
    )
    confirmed_by = factory.SubFactory(ManagerUserFactory)
    confirmed_at = factory.LazyAttribute(
        lambda obj: obj.start_datetime - timedelta(hours=24)
    )
