from django.db import models
from cieloapi.base_model import BaseModel


TIPOS_LABOR = [
    ('recoleccion', 'Recolección'),
    ('guadana', 'Guadaña'),
    ('abono', 'Abono'),
    ('varios', 'Varios'),
    ('banano', 'Banano'),
    ('cosecha', 'Cosecha'),
    ('siembra', 'Siembra'),
    ('embolsada', 'Embolsada'),
    ('auxilio_labor', 'Auxilio Labor'),
    ('auxilio_transporte', 'Auxilio Transporte'),
    ('permiso', 'Permiso'),
    ('nomina', 'Nómina'),
    ('contrato', 'Contrato'),
]

TIPOS_COBRO = [
    ('kilos', 'Kilos'),
    ('jornal', 'Jornal'),
    ('contrato', 'Contrato'),
    ('nomina', 'Nómina'),
]


class Empleado(BaseModel):
    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre completo")
    cedula = models.CharField(
        max_length=20, unique=True, blank=True, null=True, verbose_name="Cédula"
    )
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    labor = models.CharField(max_length=100, blank=True, null=True, verbose_name="Labor principal")
    jornal = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Jornal diario"
    )
    fecha_ingreso = models.DateField(blank=True, null=True, verbose_name="Fecha de ingreso")
    salario_mensual = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Salario mensual"
    )
    salario_semanal = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Salario semanal"
    )
    eps = models.CharField(max_length=100, blank=True, null=True, verbose_name="EPS")
    pension = models.CharField(max_length=100, blank=True, null=True, verbose_name="Pensión")
    arl = models.CharField(max_length=100, blank=True, null=True, verbose_name="ARL")
    caja_compensacion = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Caja de compensación"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = "empleados"
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

    def __str__(self):
        return self.nombre_completo


class ControlSemanal(BaseModel):
    empleado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT,
        related_name="registros_control", verbose_name="Empleado"
    )
    fecha_inicio = models.DateField(db_index=True, verbose_name="Fecha inicio")
    fecha_fin = models.DateField(verbose_name="Fecha fin")
    tipo_labor = models.CharField(
        max_length=30, choices=TIPOS_LABOR, db_index=True, verbose_name="Tipo labor"
    )
    tipo_cobro = models.CharField(
        max_length=20, choices=TIPOS_COBRO, verbose_name="Tipo cobro"
    )
    lote = models.CharField(max_length=100, blank=True, null=True, verbose_name="Lote")
    kilos = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Kilos"
    )
    jornales = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Jornales"
    )
    costo_unidad = models.DecimalField(
        max_digits=12, decimal_places=5, verbose_name="Costo x kilo / jornal"
    )
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor total")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    es_vale = models.BooleanField(
        default=False,
        verbose_name="Es vale",
        help_text="True = registrado en planilla de vales, False = planilla formal"
    )

    class Meta:
        db_table = "control_semanal"
        verbose_name = "Control Semanal"
        verbose_name_plural = "Control Semanal"
        indexes = [
            models.Index(fields=['empleado', 'fecha_inicio']),
            models.Index(fields=['fecha_inicio', 'tipo_labor']),
        ]

    def __str__(self):
        return f"{self.empleado} | {self.fecha_inicio} — {self.fecha_fin} | {self.get_tipo_labor_display()}"


class PrestamoEmpleado(BaseModel):
    fecha = models.DateField(db_index=True, verbose_name="Fecha préstamo")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    empleado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT,
        related_name="prestamos", verbose_name="Empleado"
    )
    concepto = models.CharField(max_length=300, verbose_name="Concepto")
    saldo = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Saldo pendiente"
    )

    class Meta:
        db_table = "prestamos_empleados"
        verbose_name = "Préstamo a empleado"
        verbose_name_plural = "Préstamos a empleados"

    def __str__(self):
        return f"{self.empleado} — ${self.valor:,.0f} ({self.fecha})"

    def recalcular_saldo(self):
        total_abonado = self.abonos.aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        self.saldo = self.valor - total_abonado
        self.save(update_fields=['saldo'])


class AbonoPrestamo(BaseModel):
    prestamo = models.ForeignKey(
        PrestamoEmpleado, on_delete=models.CASCADE,
        related_name="abonos", verbose_name="Préstamo"
    )
    fecha = models.DateField(verbose_name="Fecha abono")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    nota = models.CharField(max_length=300, blank=True, null=True, verbose_name="Nota")

    class Meta:
        db_table = "abonos_prestamos"
        verbose_name = "Abono a préstamo"
        verbose_name_plural = "Abonos a préstamos"

    def __str__(self):
        return f"Abono ${self.valor:,.0f} al préstamo de {self.prestamo.empleado} ({self.fecha})"
