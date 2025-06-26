# apps/tenants/serializers.py
from rest_framework import serializers
from .models import Tenant, TenantConfiguration


class TenantSerializer(serializers.ModelSerializer):
    usage_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'subdomain', 'domain_url', 'cnpj', 'phone', 'email',
            'address', 'city', 'state', 'zipcode', 'plan', 'status',
            'max_users', 'max_patients', 'max_storage_mb', 'logo',
            'primary_color', 'secondary_color', 'enable_sms', 'enable_whatsapp',
            'enable_video_call', 'created_at', 'trial_end_date', 'usage_stats'
        ]
        read_only_fields = ['id', 'created_at', 'usage_stats']
    
    def get_usage_stats(self, obj):
        return obj.get_usage_stats()


class TenantConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantConfiguration
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


