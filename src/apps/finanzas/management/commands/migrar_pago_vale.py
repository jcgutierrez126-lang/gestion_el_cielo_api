"""
Management command: migrar_pago_vale

Hace dos cosas:
1. Convierte egresos "Pago Vale" en Transacciones (Bancolombia → Agencia).
   Elimina el doble conteo: el vale total no es un egreso, es una transferencia.

2. Reasigna a cuenta Agencia los egresos que tenían cuenta tipo "vale"
   (gasolina, cuchillas, etc.). Esos sí son egresos reales pero su cuenta
   de origen es la Agencia, no una cuenta bancaria.

Usage:
    python manage.py migrar_pago_vale --dry-run   # Ver qué haría sin modificar
    python manage.py migrar_pago_vale              # Ejecutar la migración
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.finanzas.models import Cuenta, Egreso, Transaccion


class Command(BaseCommand):
    help = "Migra Pago Vale → Transacción y reasigna gastos de vale → cuenta Agencia"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra los registros afectados sin guardar cambios",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # ── 1. Egresos "Pago Vale" → Transacción ──────────────────────────────
        egresos_pago_vale = Egreso.objects.filter(
            Q(nombre__icontains="pago vale") | Q(categoria="no_aplica")
        ).order_by("fecha")

        total_pv = egresos_pago_vale.count()
        self.stdout.write(f"\n[1] Egresos 'Pago Vale' a convertir en Transacciones: {total_pv}")
        for e in egresos_pago_vale[:10]:
            self.stdout.write(f"    {e.fecha} | {e.nombre} | ${e.valor:,.0f}")
        if total_pv > 10:
            self.stdout.write(f"    ... y {total_pv - 10} más.")

        # ── 2. Egresos con cuenta tipo "vale" → reasignar a Agencia ───────────
        cuentas_vale = Cuenta.objects.filter(tipo="vale")
        egresos_con_vale = Egreso.objects.filter(cuenta__in=cuentas_vale).exclude(
            Q(nombre__icontains="pago vale") | Q(categoria="no_aplica")
        ).order_by("fecha")

        # También captura egresos sin cuenta (huérfanos por borrado de la cuenta vale)
        egresos_sin_cuenta = Egreso.objects.filter(cuenta__isnull=True).exclude(
            Q(nombre__icontains="pago vale") | Q(categoria="no_aplica")
        ).order_by("fecha")

        total_cv = egresos_con_vale.count() + egresos_sin_cuenta.count()
        self.stdout.write(f"\n[2] Egresos con cuenta 'vale' a reasignar a Agencia: {total_cv}")
        for e in list(egresos_con_vale[:10]) + list(egresos_sin_cuenta[:5]):
            self.stdout.write(f"    {e.fecha} | {e.nombre} | ${e.valor:,.0f} | cat: {e.categoria}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No se realizaron cambios."))
            return

        if total_pv == 0 and total_cv == 0:
            self.stdout.write(self.style.SUCCESS("Nada que migrar."))
            return

        # Buscar cuentas destino
        bancolombia = (
            Cuenta.objects.filter(tipo="bancaria", nombre__icontains="natalia").first()
            or Cuenta.objects.filter(tipo="bancaria").first()
        )
        agencia = Cuenta.objects.filter(tipo="agencia").first()

        if not agencia:
            self.stdout.write(self.style.ERROR(
                "No existe ninguna cuenta de tipo 'agencia'. Crea la cuenta Agencia primero."
            ))
            return

        if not bancolombia:
            self.stdout.write(self.style.WARNING(
                "No se encontró cuenta bancaria. Las transacciones quedarán sin cuenta origen."
            ))

        creadas = 0
        eliminadas = 0
        reasignados = 0

        with transaction.atomic():
            # Paso 1: Pago Vale → Transacción
            for e in egresos_pago_vale:
                Transaccion.objects.create(
                    fecha=e.fecha,
                    cuenta_origen=bancolombia,
                    cuenta_destino=agencia,
                    valor=e.valor,
                    observaciones=(
                        f"Pago Vale migrado desde egreso #{e.id}"
                        + (f" — {e.descripcion}" if e.descripcion else "")
                    ),
                )
                creadas += 1
            eliminadas = egresos_pago_vale.count()
            egresos_pago_vale.delete()

            # Paso 2: Egresos de gastos del vale → cuenta Agencia
            updated = egresos_con_vale.update(cuenta=agencia)
            updated2 = egresos_sin_cuenta.update(cuenta=agencia)
            reasignados = updated + updated2

        self.stdout.write(self.style.SUCCESS(
            f"\nMigración completada:\n"
            f"  {creadas} transacciones creadas (Bancolombia → Agencia)\n"
            f"  {eliminadas} egresos 'Pago Vale' eliminados\n"
            f"  {reasignados} egresos reasignados a cuenta Agencia"
        ))
