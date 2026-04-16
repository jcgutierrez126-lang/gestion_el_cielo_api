from django.db import models
from cieloapi.base_model import BaseModel


CATEGORIAS_EGRESO = [
    ('fertilizantes', 'Fertilizantes'),
    ('herbicidas', 'Herbicidas'),
    ('nomina', 'Nómina'),
    ('seguridad_social', 'Seguridad Social'),
    ('transporte', 'Transporte'),
    ('viaticos', 'Viáticos'),
    ('acueducto', 'Acueducto'),
    ('epm', 'EPM'),
    ('comsab', 'Comsab'),
    ('mantenimientos', 'Mantenimientos'),
    ('varios', 'Varios'),
    ('beneficio', 'Beneficio'),
    ('guadana', 'Guadaña'),
    ('construcciones', 'Construcciones'),
    ('impuestos', 'Impuestos'),
    ('animales', 'Animales'),
    ('siembra', 'Siembra'),
    ('herramientas', 'Herramientas'),
    ('broca', 'Broca'),
    ('roya', 'Roya'),
    ('moto', 'Moto'),
    ('prestamo_empleados', 'Préstamo empleados'),
    ('no_aplica', 'No aplica'),
    ('activos_fijos', 'Activos fijos'),
    ('banano', 'Banano'),
    ('compra_finca', 'Compra Finca'),
    ('capacitaciones', 'Capacitaciones'),
]


class Cuenta(BaseModel):
    TIPOS = [
        ('bancaria', 'Bancaria'),
        ('efectivo', 'Efectivo'),
        ('prestamo', 'Préstamo'),
        ('agencia', 'Agencia / Cooperativa'),
        ('dividendos', 'Dividendos'),
        ('vale', 'Vale'),
    ]
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    tipo = models.CharField(max_length=20, choices=TIPOS, verbose_name="Tipo")
    saldo_inicial = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Saldo inicial"
    )

    class Meta:
        db_table = "cuentas"
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"

    def __str__(self):
        return self.nombre


class Proveedor(BaseModel):
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    celular = models.CharField(max_length=20, blank=True, null=True, verbose_name="Celular")
    cedula_nit = models.CharField(max_length=30, blank=True, null=True, verbose_name="Cédula / NIT")
    direccion = models.CharField(max_length=200, blank=True, null=True, verbose_name="Dirección")
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    comentarios = models.TextField(blank=True, null=True, verbose_name="Comentarios")

    class Meta:
        db_table = "proveedores"
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre


class Egreso(BaseModel):
    ESTADOS = [
        ('pagada', 'Pagada'),
        ('pendiente', 'Pendiente'),
        ('parcial', 'Parcial'),
    ]
    fecha = models.DateField(db_index=True, verbose_name="Fecha")
    nombre = models.CharField(max_length=200, verbose_name="Nombre / Concepto")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    cantidad = models.DecimalField(
        max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="Cantidad"
    )
    unidad = models.CharField(max_length=50, blank=True, null=True, verbose_name="Unidad")
    valor = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor")
    cuenta = models.ForeignKey(
        Cuenta, on_delete=models.PROTECT, related_name="egresos", verbose_name="Cuenta"
    )
    categoria = models.CharField(
        max_length=50, choices=CATEGORIAS_EGRESO, db_index=True, verbose_name="Categoría"
    )
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="egresos", verbose_name="Proveedor"
    )
    nit_proveedor_destino = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="NIT / Destino"
    )
    facturado_a = models.CharField(max_length=100, blank=True, null=True, verbose_name="Facturado a")
    abono_deuda = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Abono a deuda"
    )
    restante = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Restante"
    )
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='pagada', verbose_name="Estado"
    )

    class Meta:
        db_table = "egresos"
        verbose_name = "Egreso"
        verbose_name_plural = "Egresos"
        indexes = [
            models.Index(fields=['fecha', 'categoria']),
        ]

    def __str__(self):
        return f"{self.fecha} — {self.nombre} (${self.valor:,.0f})"


class Ingreso(BaseModel):
    fecha = models.DateField(db_index=True, verbose_name="Fecha")
    descripcion = models.CharField(max_length=300, verbose_name="Descripción")
    valor = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor")
    cuenta_destino = models.ForeignKey(
        Cuenta, on_delete=models.PROTECT, related_name="ingresos", verbose_name="Cuenta destino"
    )
    origen = models.CharField(max_length=200, blank=True, null=True, verbose_name="Origen")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        db_table = "ingresos"
        verbose_name = "Ingreso"
        verbose_name_plural = "Ingresos"

    def __str__(self):
        return f"{self.fecha} — {self.descripcion} (${self.valor:,.0f})"


class Transaccion(BaseModel):
    fecha = models.DateField(db_index=True, verbose_name="Fecha")
    cuenta_origen = models.ForeignKey(
        Cuenta, on_delete=models.PROTECT, related_name="salidas",
        null=True, blank=True, verbose_name="Cuenta origen"
    )
    cuenta_destino = models.ForeignKey(
        Cuenta, on_delete=models.PROTECT, related_name="entradas", verbose_name="Cuenta destino"
    )
    valor = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        db_table = "transacciones"
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"

    def __str__(self):
        origen = self.cuenta_origen.nombre if self.cuenta_origen else "—"
        return f"{self.fecha} | {origen} → {self.cuenta_destino.nombre} (${self.valor:,.0f})"


class Observacion(BaseModel):
    fecha = models.DateField(db_index=True, verbose_name="Fecha")
    observacion = models.TextField(verbose_name="Observación")

    class Meta:
        db_table = "observaciones"
        verbose_name = "Observación"
        verbose_name_plural = "Observaciones"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha} — {self.observacion[:60]}"
