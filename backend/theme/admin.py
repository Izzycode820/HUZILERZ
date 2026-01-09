from django.contrib import admin
from .models import (
    Template, TemplateVersion, TemplateAsset, TemplateCategory,
    TemplateCustomization, CustomizationHistory
)


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'price_tier', 'status', 'version', 'created_at']
    list_filter = ['template_type', 'price_tier', 'status', 'created_at']
    search_fields = ['name', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(TemplateVersion)
class TemplateVersionAdmin(admin.ModelAdmin):
    list_display = ['template', 'version', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['template__name', 'version']


@admin.register(TemplateAsset)
class TemplateAssetAdmin(admin.ModelAdmin):
    list_display = ['template', 'asset_type', 'file_name', 'created_at']
    list_filter = ['asset_type', 'created_at']
    search_fields = ['template__name', 'file_name']


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'template_type', 'is_featured', 'sort_order']
    list_filter = ['template_type', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}


