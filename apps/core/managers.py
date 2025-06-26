# apps/core/managers.py
from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """
    Manager que filtra automaticamente registros soft-deleted
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, deleted_at__isnull=True)
    
    def with_deleted(self):
        """Retorna todos os registros, incluindo os deletados"""
        return super().get_queryset()
    
    def deleted_only(self):
        """Retorna apenas os registros deletados"""
        return super().get_queryset().filter(is_active=False, deleted_at__isnull=False)


class TenantAwareManager(SoftDeleteManager):
    """
    Manager que adiciona isolamento por tenant
    """
    def __init__(self, *args, **kwargs):
        self._tenant = None
        super().__init__(*args, **kwargs)
    
    def set_tenant(self, tenant):
        """Define o tenant atual para filtros automáticos"""
        self._tenant = tenant
        return self
    
    def get_queryset(self):
        qs = super().get_queryset()
        if self._tenant:
            qs = qs.filter(tenant=self._tenant)
        return qs
    
    def for_tenant(self, tenant):
        """Filtra explicitamente por tenant"""
        return self.get_queryset().filter(tenant=tenant)
    
    def create(self, **kwargs):
        """Override para adicionar tenant automaticamente"""
        if self._tenant and 'tenant' not in kwargs:
            kwargs['tenant'] = self._tenant
        return super().create(**kwargs)


class NotificationManager(TenantAwareManager):
    """
    Manager específico para notificações
    """
    def unread(self):
        return self.get_queryset().filter(is_read=False)
    
    def read(self):
        return self.get_queryset().filter(is_read=True)
    
    def for_user(self, user):
        return self.get_queryset().filter(recipient=user)
    
    def pending_send(self):
        """Notificações pendentes de envio"""
        return self.get_queryset().filter(
            sent_at__isnull=True,
            scheduled_for__lte=timezone.now()
        )
    
    def by_channel(self, channel):
        return self.get_queryset().filter(channel=channel)
    
    def mark_as_read(self, user=None):
        """Marca notificações como lidas"""
        qs = self.get_queryset()
        if user:
            qs = qs.filter(recipient=user)
        
        return qs.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )


class SystemLogManager(SoftDeleteManager):
    """
    Manager para logs do sistema
    """
    def for_tenant(self, tenant):
        return self.get_queryset().filter(tenant=tenant)
    
    def for_user(self, user):
        return self.get_queryset().filter(user=user)
    
    def by_level(self, level):
        return self.get_queryset().filter(level=level)
    
    def by_action(self, action):
        return self.get_queryset().filter(action=action)
    
    def errors(self):
        return self.get_queryset().filter(level__in=['error', 'critical'])
    
    def recent(self, days=7):
        """Logs recentes"""
        since = timezone.now() - timezone.timedelta(days=days)
        return self.get_queryset().filter(created_at__gte=since)
    
    def create_log(self, level, action, description, tenant=None, user=None, 
                   ip_address=None, user_agent=None, extra_data=None):
        """Cria um log do sistema"""
        return self.create(
            level=level,
            action=action,
            description=description,
            tenant=tenant,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data or {}
        )


class ConfigurationManager(TenantAwareManager):
    """
    Manager para configurações do sistema
    """
    def get_value(self, key, default=None):
        """Obtém o valor de uma configuração"""
        try:
            config = self.get_queryset().get(key=key)
            return config.value
        except self.model.DoesNotExist:
            return default
    
    def set_value(self, key, value, description=''):
        """Define o valor de uma configuração"""
        config, created = self.get_queryset().get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if not created:
            config.value = value
            config.description = description
            config.save()
        return config
    
    def get_json_value(self, key, default=None):
        """Obtém valor JSON de uma configuração"""
        import json
        value = self.get_value(key)
        if value is None:
            return default
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default
    
    def set_json_value(self, key, value, description=''):
        """Define valor JSON para uma configuração"""
        import json
        json_value = json.dumps(value)
        return self.set_value(key, json_value, description)