# apps/tenants/utils.py
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.tenants.models import Tenant, TenantDomain
import re
import json
import logging

logger = logging.getLogger(__name__)


def get_tenant_from_request(request):
    """
    Obtém o tenant a partir da requisição HTTP
    """
    host = request.get_host().lower()
    
    # Tentar cache primeiro
    cache_key = f"tenant_lookup:{host}"
    tenant = cache.get(cache_key)
    if tenant:
        return tenant
    
    tenant = None
    
    # 1. Buscar por domínio customizado
    try:
        domain = TenantDomain.objects.select_related('tenant').get(
            domain=host,
            is_verified=True,
            tenant__is_active=True
        )
        tenant = domain.tenant
    except TenantDomain.DoesNotExist:
        pass
    
    # 2. Buscar por subdomínio
    if not tenant and '.' in host:
        subdomain = host.split('.')[0]
        try:
            tenant = Tenant.objects.get(
                slug=subdomain,
                is_active=True
            )
        except Tenant.DoesNotExist:
            pass
    
    # Cache por 5 minutos
    if tenant:
        cache.set(cache_key, tenant, 300)
    
    return tenant


def validate_tenant_slug(slug):
    """
    Valida se o slug do tenant é válido
    """
    # Padrão: apenas letras minúsculas, números e hífens
    if not re.match(r'^[a-z0-9-]+$', slug):
        raise ValidationError(
            'Slug deve conter apenas letras minúsculas, números e hífens'
        )
    
    # Não pode começar ou terminar com hífen
    if slug.startswith('-') or slug.endswith('-'):
        raise ValidationError(
            'Slug não pode começar ou terminar com hífen'
        )
    
    # Verificar palavras reservadas
    reserved_words = [
        'www', 'api', 'admin', 'app', 'mail', 'ftp', 'localhost',
        'staging', 'test', 'dev', 'development', 'production',
        'support', 'help', 'blog', 'docs', 'status'
    ]
    
    if slug in reserved_words:
        raise ValidationError(f'"{slug}" é uma palavra reservada')
    
    return True


def generate_tenant_slug(name):
    """
    Gera um slug único para o tenant baseado no nome
    """
    import unicodedata
    
    # Normalizar e remover acentos
    slug = unicodedata.normalize('NFD', name.lower())
    slug = ''.join(c for c in slug if unicodedata.category(c) != 'Mn')
    
    # Substituir espaços e caracteres especiais por hífen
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    
    # Garantir que é único
    original_slug = slug
    counter = 1
    
    while Tenant.objects.filter(slug=slug).exists():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    # Validar
    validate_tenant_slug(slug)
    
    return slug


def check_tenant_limits(tenant, resource_type, additional=1):
    """
    Verifica se o tenant está dentro dos limites de recursos
    """
    usage = get_tenant_usage(tenant)
    current = usage.get(resource_type, 0)
    limit = getattr(tenant, f'max_{resource_type}', 0)
    
    if (current + additional) > limit:
        return False, {
            'current': current,
            'limit': limit,
            'requested': additional,
            'available': max(0, limit - current)
        }
    
    return True, {
        'current': current,
        'limit': limit,
        'requested': additional,
        'available': limit - current - additional
    }


def get_tenant_usage(tenant):
    """
    Obtém o uso atual de recursos do tenant
    """
    cache_key = f"tenant_usage:{tenant.id}"
    usage = cache.get(cache_key)
    
    if not usage:
        # Calcular uso atual
        from apps.users.models import User
        from apps.patients.models import Patient
        
        usage = {
            'users': User.objects.filter(tenant=tenant, is_active=True).count(),
            'patients': Patient.objects.filter(tenant=tenant, is_active=True).count(),
            'storage_gb': calculate_tenant_storage(tenant),
        }
        
        # Cache por 10 minutos
        cache.set(cache_key, usage, 600)
    
    return usage


def calculate_tenant_storage(tenant):
    """
    Calcula o uso de storage do tenant em GB
    """
    # TODO: Implementar cálculo real de storage
    # Por enquanto retorna 0
    return 0


def invalidate_tenant_cache(tenant):
    """
    Invalida todos os caches relacionados ao tenant
    """
    cache_patterns = [
        f"tenant_usage:{tenant.id}",
        f"tenant_lookup:{tenant.slug}.*",
        f"tenant_settings:{tenant.id}",
        f"tenant_modules:{tenant.id}",
    ]
    
    # Invalidar domínios associados
    for domain in tenant.domains.all():
        cache.delete(f"tenant_lookup:{domain.domain}")
    
    # Invalidar outros caches
    for pattern in cache_patterns:
        if '*' in pattern:
            # Para padrões com wildcard, seria necessário usar Redis ou implementar lógica customizada
            pass
        else:
            cache.delete(pattern)


def get_tenant_setting(tenant, key, default=None):
    """
    Obtém uma configuração específica do tenant
    """
    cache_key = f"tenant_setting:{tenant.id}:{key}"
    value = cache.get(cache_key)
    
    if value is None:
        from apps.core.models import Configuration
        
        try:
            config = Configuration.objects.get(tenant=tenant, key=key)
            value = config.value
            
            # Cache por 1 hora
            cache.set(cache_key, value, 3600)
        except Configuration.DoesNotExist:
            value = default
    
    return value


def set_tenant_setting(tenant, key, value, description=''):
    """
    Define uma configuração específica do tenant
    """
    from apps.core.models import Configuration
    
    config, created = Configuration.objects.get_or_create(
        tenant=tenant,
        key=key,
        defaults={'value': str(value), 'description': description}
    )
    
    if not created:
        config.value = str(value)
        config.description = description
        config.save()
    
    # Atualizar cache
    cache_key = f"tenant_setting:{tenant.id}:{key}"
    cache.set(cache_key, str(value), 3600)
    
    return config


def is_module_enabled(tenant, module_name):
    """
    Verifica se um módulo está habilitado para o tenant
    """
    if not tenant.enabled_modules:
        return False
    
    return module_name in tenant.enabled_modules


def get_tenant_modules(tenant):
    """
    Retorna lista de módulos habilitados para o tenant
    """
    cache_key = f"tenant_modules:{tenant.id}"
    modules = cache.get(cache_key)
    
    if modules is None:
        modules = tenant.enabled_modules or []
        cache.set(cache_key, modules, 3600)
    
    return modules


def tenant_url(tenant, path=''):
    """
    Gera URL completa para um tenant
    """
    domain = tenant.get_primary_domain()
    
    if domain:
        protocol = 'https' if domain.ssl_enabled else 'http'
        return f"{protocol}://{domain.domain}{path}"
    else:
        # Fallback para subdomínio
        base_domain = getattr(settings, 'BASE_DOMAIN', 'localhost:8000')
        protocol = 'https' if getattr(settings, 'USE_SSL', False) else 'http'
        return f"{protocol}://{tenant.slug}.{base_domain}{path}"


def create_tenant_with_defaults(name, slug=None, admin_email=None, **kwargs):
    """
    Cria um novo tenant com configurações padrão
    """
    from apps.tenants.models import TenantSettings
    
    if not slug:
        slug = generate_tenant_slug(name)
    
    # Criar tenant
    tenant_data = {
        'name': name,
        'slug': slug,
        'email': admin_email or f'admin@{slug}.com',
        'subscription_status': 'trial',
        'trial_end': timezone.now() + timezone.timedelta(days=30),
        'enabled_modules': [
            'patients', 'scheduling', 'medical_records',
            'family_portal', 'basic_financial', 'communication'
        ],
        **kwargs
    }
    
    tenant = Tenant.objects.create(**tenant_data)
    
    # Criar configurações padrão
    TenantSettings.objects.create(
        tenant=tenant,
        working_days=[0, 1, 2, 3, 4],  # Segunda a sexta
        working_hours_start='08:00',
        working_hours_end='18:00',
        appointment_duration=50,
        advance_booking_days=30,
        cancellation_hours=24,
        email_notifications=True,
        reminder_hours_before=24,
    )
    
    # Criar domínio padrão se especificado
    if 'domain' in kwargs:
        from apps.tenants.models import TenantDomain
        TenantDomain.objects.create(
            tenant=tenant,
            domain=kwargs['domain'],
            is_primary=True,
            is_verified=False
        )
    
    logger.info(f"Tenant created: {tenant.name} ({tenant.slug})")
    
    return tenant


def tenant_backup_data(tenant):
    """
    Gera backup dos dados do tenant
    """
    # TODO: Implementar backup completo
    backup_data = {
        'tenant_info': {
            'id': str(tenant.id),
            'name': tenant.name,
            'slug': tenant.slug,
            'created_at': tenant.created_at.isoformat(),
        },
        'timestamp': timezone.now().isoformat(),
        'version': '1.0'
    }
    
    return backup_data


def validate_tenant_subscription(tenant):
    """
    Valida o status da assinatura do tenant
    """
    now = timezone.now()
    
    # Verificar se trial expirou
    if (tenant.subscription_status == 'trial' and 
        tenant.trial_end and 
        tenant.trial_end < now):
        
        tenant.subscription_status = 'expired'
        tenant.save()
        return False
    
    # Verificar se assinatura expirou
    if (tenant.subscription_status == 'active' and 
        tenant.subscription_end and 
        tenant.subscription_end < now):
        
        tenant.subscription_status = 'expired'
        tenant.save()
        return False
    
    return tenant.subscription_status in ['trial', 'active']