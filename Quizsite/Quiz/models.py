from django.db import models


class UploadedMaterial(models.Model):
    material = models.FileField("Учебный материал", upload_to="media/")
    uploaded_at = models.DateTimeField("Дата загрузки", auto_now_add=True)

    class Meta:
        verbose_name = "загруженный материал"
        verbose_name_plural = "загруженные материалы"

    def __str__(self):
        return self.material.name or f"Загруженный материал №{self.pk}"
