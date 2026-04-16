from django.db import models
from cieloapi.base_model import BaseModel
from apps.finanzas.models import Cuenta


TIPOS_CAFE = [
    ('pergamino_seco', 'Pergamino Seco'),
    ('pasilla', 'Pasilla'),
    ('corriente', 'Corriente'),
    ('cereza', 'Cereza'),
    ('verde', 'Verde'),
]

CALIDADES_FLORACION = [
    ('buena', 'Buena'),
    ('regular', 'Regular'),
    ('muy_buena', 'Muy buena'),
    ('excelente', 'Excelente'),
]

TIPOS_PLATANO = [
    ('banano_extra', 'Banano Extra'),
    ('banano_primera', 'Banano Primera'),
    ('banano_segunda', 'Banano Segunda'),
    ('platano_extra', 'Plátano Extra x dedo'),
    ('platano_segunda', 'Plátano Segunda x dedo'),
]

PRESENTACIONES_TOSTADO = [
    ('250g', '250 gramos'),
    ('500g', '500 gramos'),
    ('2500g', '2.5 kg'),
]


class Lote(BaseModel):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del lote")
    variedad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Variedad")
    año_siembra = models.CharField(max_length=50, blank=True, null=True, verbose_name="Año siembra / zoca")
    proxima_renovacion = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Próxima renovación"
    )
    num_arboles = models.IntegerField(default=0, verbose_name="Número de árboles")
    gramos_abono_palo = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Gramos abono / palo"
    )
    bultos_produccion = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Bultos producción"
    )
    bultos_urea = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Bultos urea"
    )
    bultos_dap = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Bultos DAP"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = "lotes"
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"

    def __str__(self):
        return self.nombre


class VentaCafe(BaseModel):
    fecha = models.DateField(db_index=True, verbose_name="Fecha")
    kilos = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kilos")
    cargas = models.DecimalField(max_digits=8, decimal_places=3, verbose_name="Cargas")
    tipo_cafe = models.CharField(
        max_length=20, choices=TIPOS_CAFE, db_index=True, verbose_name="Tipo de café"
    )
    factor = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Factor"
    )
    precio_kilo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio x kilo")
    precio_carga = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Precio x carga"
    )
    comprador = models.CharField(max_length=100, verbose_name="Comprador")
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor total")
    deduccion = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True, verbose_name="Deducción"
    )
    retefuente = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, blank=True, null=True, verbose_name="Retefuente"
    )
    valor_neto = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor neto")
    cuenta_destino = models.ForeignKey(
        Cuenta, on_delete=models.PROTECT, related_name="ventas_cafe", verbose_name="Cuenta destino"
    )
    facturado_a = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Facturado a"
    )
    conversion_cereza_seco = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Conversión cereza/seco"
    )
    beneficio = models.CharField(max_length=100, blank=True, null=True, verbose_name="Beneficio")
    transportador = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Transportador"
    )
    valor_transporte = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Valor transporte"
    )

    class Meta:
        db_table = "ventas_cafe"
        verbose_name = "Venta de Café"
        verbose_name_plural = "Ventas de Café"

    def __str__(self):
        return f"{self.fecha} — {self.kilos} kg {self.get_tipo_cafe_display()} (${self.valor_neto:,.0f})"


class VentaCafeTostado(BaseModel):
    TIPOS_MOLIDO = [('molido', 'Molido'), ('grano', 'Grano')]

    fecha_venta = models.DateField(db_index=True, verbose_name="Fecha venta")
    cliente = models.CharField(max_length=200, blank=True, null=True, verbose_name="Cliente")
    cantidad = models.IntegerField(verbose_name="Cantidad (unidades)")
    presentacion = models.CharField(
        max_length=10, choices=PRESENTACIONES_TOSTADO, verbose_name="Presentación"
    )
    tipo_cafe = models.CharField(
        max_length=10, choices=TIPOS_MOLIDO, verbose_name="Molido o Grano"
    )
    seleccionado = models.BooleanField(default=False, verbose_name="Seleccionado")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")
    cuenta_destino = models.ForeignKey(
        Cuenta, on_delete=models.PROTECT, related_name="ventas_cafe_tostado",
        verbose_name="Cuenta destino"
    )
    fecha_pago = models.DateField(blank=True, null=True, verbose_name="Fecha pago")

    class Meta:
        db_table = "ventas_cafe_tostado"
        verbose_name = "Venta Café Tostado"
        verbose_name_plural = "Ventas Café Tostado"

    def __str__(self):
        return f"{self.fecha_venta} — {self.cantidad} und {self.get_presentacion_display()} (${self.valor:,.0f})"


class Floracion(BaseModel):
    fecha = models.DateField(db_index=True, verbose_name="Fecha")
    lote = models.ForeignKey(
        Lote, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="floraciones", verbose_name="Lote"
    )
    calidad = models.CharField(
        max_length=20, choices=CALIDADES_FLORACION, verbose_name="Calidad de floración"
    )
    abonada_ideal = models.BooleanField(null=True, blank=True, verbose_name="Abonada ideal")
    broca_ideal = models.BooleanField(null=True, blank=True, verbose_name="Broca ideal")
    roya_ideal = models.BooleanField(null=True, blank=True, verbose_name="Roya ideal")

    class Meta:
        db_table = "floraciones"
        verbose_name = "Floración"
        verbose_name_plural = "Floraciones"
        ordering = ['-fecha']

    def __str__(self):
        lote = self.lote.nombre if self.lote else "Toda la finca"
        return f"{self.fecha} — {lote} ({self.get_calidad_display()})"


class MezclaAbono(BaseModel):
    fecha = models.DateField(db_index=True, verbose_name="Fecha")
    formula = models.CharField(max_length=300, verbose_name="Fórmula")
    lote = models.ForeignKey(
        Lote, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="mezclas_abono", verbose_name="Lote"
    )
    num_arboles = models.IntegerField(blank=True, null=True, verbose_name="Número de árboles")
    gramos_por_arbol = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Gramos por árbol"
    )
    costo_total = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Costo total"
    )

    class Meta:
        db_table = "mezclas_abono"
        verbose_name = "Mezcla de Abono"
        verbose_name_plural = "Mezclas de Abono"

    def __str__(self):
        return f"{self.fecha} — {self.formula}"


class MezclaAbonoFertilizante(BaseModel):
    mezcla = models.ForeignKey(
        MezclaAbono, on_delete=models.CASCADE,
        related_name="fertilizantes", verbose_name="Mezcla"
    )
    fertilizante = models.CharField(max_length=100, verbose_name="Fertilizante")
    num_bultos = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Número de bultos")
    precio_bulto = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Precio x bulto"
    )

    class Meta:
        db_table = "mezclas_abono_fertilizantes"
        verbose_name = "Fertilizante en mezcla"
        verbose_name_plural = "Fertilizantes en mezcla"

    def __str__(self):
        return f"{self.fertilizante} — {self.num_bultos} bultos"


class VentaBanano(BaseModel):
    fecha = models.DateField(db_index=True, verbose_name="Fecha")
    tipo_platano = models.CharField(
        max_length=30, choices=TIPOS_PLATANO, db_index=True, verbose_name="Tipo"
    )
    kilos = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kilos")
    precio_kilo = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Precio x kilo")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor total")
    cuenta_destino = models.ForeignKey(
        Cuenta, on_delete=models.PROTECT, related_name="ventas_banano", verbose_name="Cuenta destino"
    )
    facturado_a = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Facturado a"
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        db_table = "ventas_banano"
        verbose_name = "Venta de Banano"
        verbose_name_plural = "Ventas de Banano"

    def __str__(self):
        return f"{self.fecha} — {self.kilos} kg {self.get_tipo_platano_display()} (${self.valor_total:,.0f})"
