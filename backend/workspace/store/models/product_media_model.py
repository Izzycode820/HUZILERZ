"""
ProductMediaGallery Junction Model

Many-to-Many through table for Product-Media relationship with ordering
Allows:
- Ordered media gallery (position field)
- Multiple media per product with limits enforced
- Easy querying and management
"""

from django.db import models
from django.core.exceptions import ValidationError


class ProductMediaGallery(models.Model):
    """
    Junction table for Product <-> MediaUpload relationship (media gallery)

    Features:
    - Ordering via position field
    - Automatic limit enforcement (5 videos, 2 3D models, unlimited images)
    - Unique constraint prevents duplicate media per product
    """

    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='gallery_items'
    )

    media = models.ForeignKey(
        'medialib.MediaUpload',
        on_delete=models.CASCADE,
        related_name='product_associations'
    )

    position = models.PositiveIntegerField(
        default=0,
        help_text="Display order in gallery (0 = first)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'created_at']
        unique_together = [['product', 'media']]
        verbose_name = 'Product Media Gallery'
        verbose_name_plural = 'Product Media Gallery'
        indexes = [
            models.Index(fields=['product', 'position']),
            models.Index(fields=['media']),
        ]
        db_table = 'store_product_media_gallery'

    def __str__(self):
        return f"{self.product.name} - {self.media.media_type} #{self.position}"

    def clean(self):
        """
        Validate media limits per product:
        - Videos: Max 5
        - 3D Models: Max 2
        - Images: Unlimited
        """
        if not self.pk:  # Only validate on creation
            # Count existing media of this type
            existing_count = ProductMediaGallery.objects.filter(
                product=self.product,
                media__media_type=self.media.media_type
            ).count()

            # Enforce limits
            if self.media.media_type == 'video' and existing_count >= 5:
                raise ValidationError(
                    f"Maximum 5 videos allowed per product. Currently has {existing_count}."
                )

            if self.media.media_type == '3d_model' and existing_count >= 2:
                raise ValidationError(
                    f"Maximum 2 3D models allowed per product. Currently has {existing_count}."
                )

    def save(self, *args, **kwargs):
        """Run validation before save"""
        self.full_clean()
        super().save(*args, **kwargs)
