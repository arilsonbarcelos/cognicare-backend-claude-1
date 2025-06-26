# apps/tenants/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Tenant, TenantConfiguration
from .serializers import TenantSerializer, TenantConfigurationSerializer


class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Superadmin pode ver todos os tenants
        if self.request.user.is_superuser:
            return Tenant.objects.all()
        # Usuários normais só veem seu próprio tenant
        return Tenant.objects.filter(schema_name=self.request.tenant.schema_name)
    
    @action(detail=True, methods=['get', 'put'])
    def configuration(self, request, pk=None):
        """
        Endpoint para gerenciar configurações do tenant
        """
        tenant = self.get_object()
        
        if request.method == 'GET':
            config, created = TenantConfiguration.objects.get_or_create(tenant=tenant)
            serializer = TenantConfigurationSerializer(config)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            config, created = TenantConfiguration.objects.get_or_create(tenant=tenant)
            serializer = TenantConfigurationSerializer(config, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """
        Endpoint para estatísticas de uso do tenant
        """
        tenant = self.get_object()
        stats = tenant.get_usage_stats()
        
        # Adicionar informações de limites
        stats.update({
            'limits': {
                'max_users': tenant.max_users,
                'max_patients': tenant.max_patients,
                'max_storage_mb': tenant.max_storage_mb
            },
            'usage_percentage': {
                'users': (stats['users'] / tenant.max_users * 100) if tenant.max_users > 0 else 0,
                'patients': (stats['patients'] / tenant.max_patients * 100) if tenant.max_patients > 0 else 0,
            }
        })
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def upgrade_plan(self, request, pk=None):
        """
        Endpoint para upgrade de plano
        """
        tenant = self.get_object()
        new_plan = request.data.get('plan')
        
        if new_plan not in ['basic', 'premium', 'enterprise']:
            return Response(
                {'error': 'Plano inválido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Definir limites baseados no plano
        plan_limits = {
            'basic': {'max_users': 5, 'max_patients': 100, 'max_storage_mb': 1024},
            'premium': {'max_users': 20, 'max_patients': 500, 'max_storage_mb': 5120},
            'enterprise': {'max_users': 100, 'max_patients': 2000, 'max_storage_mb': 20480},
        }
        
        tenant.plan = new_plan
        tenant.max_users = plan_limits[new_plan]['max_users']
        tenant.max_patients = plan_limits[new_plan]['max_patients']
        tenant.max_storage_mb = plan_limits[new_plan]['max_storage_mb']
        tenant.save()
        
        serializer = self.get_serializer(tenant)
        return Response(serializer.data)
