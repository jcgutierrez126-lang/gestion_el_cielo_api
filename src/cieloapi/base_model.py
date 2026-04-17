from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Fecha de actualización")
    status = models.BooleanField(default=True, verbose_name="Estado")
    
    class Meta:
        abstract = True
        verbose_name = 'BaseModel'
        verbose_name_plural = 'BaseModels'
    
    def is_active_status(self):
        return self.is_active
    