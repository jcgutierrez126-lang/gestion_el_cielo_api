from django.core.management.base import BaseCommand
from apps.integraciones.models import APIKey


class Command(BaseCommand):
    help = "Genera una nueva API Key para un cliente de servicio (ej: bot de Teams)"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help='Nombre del cliente (ej: "teams-bot")')

    def handle(self, *args, **options):
        name = options["name"]

        if APIKey.objects.filter(name=name).exists():
            self.stdout.write(self.style.ERROR(f'Ya existe una API Key con el nombre "{name}".'))
            self.stdout.write('Usa el admin de Django para desactivarla y crea una nueva.')
            return

        instance, raw_key = APIKey.create_key(name=name)

        self.stdout.write(self.style.SUCCESS("\n=== API Key generada exitosamente ==="))
        self.stdout.write(f"  Nombre:  {instance.name}")
        self.stdout.write(f"  Prefijo: {instance.key_prefix}...")
        self.stdout.write(self.style.WARNING("\n  KEY (guardar ahora, no se vuelve a mostrar):"))
        self.stdout.write(self.style.WARNING(f"  {raw_key}"))
        self.stdout.write("\nConfigura esta key en las variables de entorno del bot:")
        self.stdout.write("  CORONA_API_KEY=" + raw_key)
        self.stdout.write(self.style.SUCCESS("\n=====================================\n"))
