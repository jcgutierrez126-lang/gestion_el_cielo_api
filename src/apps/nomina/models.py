from django.db import models
from cieloapi.base_model import BaseModel
from apps.produccion.models import Lote


class TipoLabor(BaseModel):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = "tipos_labor"
        ordering = ['nombre']
        verbose_name = "Tipo de labor"
        verbose_name_plural = "Tipos de labor"

    def __str__(self):
        return self.nombre


class TipoCobro(BaseModel):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = "tipos_cobro"
        ordering = ['nombre']
        verbose_name = "Tipo de cobro"
        verbose_name_plural = "Tipos de cobro"

    def __str__(self):
        return self.nombre


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
    tipo_labor = models.ForeignKey(
        TipoLabor, on_delete=models.PROTECT,
        verbose_name="Tipo labor"
    )
    tipo_cobro = models.ForeignKey(
        TipoCobro, on_delete=models.PROTECT,
        verbose_name="Tipo cobro"
    )
    lote = models.ForeignKey(
        Lote, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="Lote"
    )
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
        return f"{self.empleado} | {self.fecha_inicio} — {self.fecha_fin} | {self.tipo_labor}"


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


class ControlDiario(BaseModel):
    semana_ref = models.CharField(max_length=150, blank=True, default='', verbose_name='Semana referencia')
    fecha = models.DateField(db_index=True, verbose_name='Fecha')
    dia = models.CharField(max_length=20, blank=True, default='', verbose_name='Día')
    nombre = models.CharField(max_length=200, verbose_name='Nombre trabajador')
    lote = models.CharField(max_length=100, blank=True, default='', verbose_name='Lote')
    labor = models.CharField(max_length=150, verbose_name='Labor')
    cantidad = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Cantidad/Kilos'
    )
    tipo_cobro = models.CharField(max_length=50, blank=True, default='', verbose_name='Tipo cobro')
    valor = models.DecimalField(
        max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='Valor'
    )

    class Meta:
        db_table = 'control_diario'
        verbose_name = 'Control Diario'
        verbose_name_plural = 'Control Diario'
        ordering = ['-fecha', 'nombre']

    def __str__(self):
        return f"{self.nombre} | {self.fecha} ({self.dia}) | {self.labor}"


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
