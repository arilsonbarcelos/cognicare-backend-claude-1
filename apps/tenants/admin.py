# apps/tenants/admin.py
from django.contrib import admin
from .models import Tenant, TenantConfiguration


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'subdomain', 'plan', 'status', 'created_at']
    list_filter = ['plan', 'status', 'created_at']
    search_fields = ['name', 'subdomain', 'cnpj']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'subdomain', 'domain_url')
        }),
        ('Dados da Clínica', {
            'fields': ('cnpj', 'phone', 'email', 'address', 'city', 'state', 'zipcode')
        }),
        ('Plano e Limites', {
            'fields': ('plan', 'status', 'max_users', 'max_patients', 'max_storage_mb', 'trial_end_date')
        }),
        ('Personalização', {
            'fields': ('logo', 'primary_color', 'secondary_color')
        }),
        ('Funcionalidades', {
            'fields': ('enable_sms', 'enable_whatsapp', 'enable_video_call')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TenantConfiguration)
class TenantConfigurationAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'appointment_duration_default', 'currency', 'report_frequency']
    list_filter = ['currency', 'report_frequency']
