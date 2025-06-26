# apps/tenants/middleware.py
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.cache import patch_cache_control
from django.core.cache import cache
from apps.tenants.models import Tenant, TenantDomain
from apps.tenants.utils import get_tenant_from_request
import threading
import logging

logger = logging.getLogger(__name__)

# Thread local storage para o tenant atual
_thread_locals = threading.local()


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware principal para gerenciar multi-tenancy
    """
    
    def process_request(self, request):
        """
        Processa a requisição para identificar e configurar o tenant
        """
        # Obter tenant baseado no domínio ou subdomínio
        tenant = self._get_tenant_from_request(request)
        
        if not tenant:
            # Se não encontrou tenant, redireciona para página de erro ou landing
            if self._is_api_request(request):
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Tenant not found',
                    'message': 'Invalid domain or tenant not active'
                }, status=404)
            else:
                # Redireciona para página de tenant não encontrado
                logger.warning(f"Tenant not found for domain: {request.get_host()}")
                raise Http404("Tenant not found")
        
        # Verificar se o tenant está ativo
        if not tenant.is_active or tenant.subscription_status not in ['trial', 'active']:
            if self._is_api_request(request):
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Tenant inactive',
                    'message': 'Tenant subscription is not active'
                }, status=403)
            else:
                # Redireciona para página de tenant suspenso
                return HttpResponseRedirect(reverse('tenant_suspended'))
        
        # Configurar tenant na requisição e thread local
        request.tenant = tenant
        set_current_tenant(tenant)
        
        # Adicionar informações do tenant no contexto
        request.tenant_context = {
            'name': tenant.name,
            'slug': tenant.slug,
            'logo': tenant.logo.url if tenant.logo else None,
            'primary_color': tenant.primary_color,
            'secondary_color': tenant.secondary_color,
            'enabled_modules': tenant.enabled_modules,
        }
        
        # Log da atividade
        logger.debug(f"Tenant set: {tenant.name} ({tenant.slug})")
    
    def process_response(self, request, response):
        """
        Processa a resposta para adicionar headers específicos do tenant
        """
        if hasattr(request, 'tenant'):
            # Adicionar headers customizados
            response['X-Tenant-ID'] = str(request.tenant.id)
            response['X-Tenant-Slug'] = request.tenant.slug
            
            # Configurar cache baseado no tenant
            if response.status_code == 200:
                patch_cache_control(response, private=True, max_age=300)
        
        return response
    
    def process_exception(self, request, exception):
        """
        Processa exceções para log específico do tenant
        """
        if hasattr(request, 'tenant'):
            logger.error(
                f"Exception in tenant {request.tenant.slug}: {str(exception)}",
                extra={'tenant_id': request.tenant.id}
            )
        return None
    
    def _get_tenant_from_request(self, request):
        """
        Obtém o tenant baseado na requisição
        """
        # Cache key baseado no host
        host = request.get_host().lower()
        cache_key = f"tenant_domain:{host}"
        
        # Tentar obter do cache primeiro
        tenant = cache.get(cache_key)
        if tenant:
            return tenant
        
        try:
            # Buscar por domínio exato
            domain = TenantDomain.objects.select_related('tenant').get(
                domain=host,
                is_verified=True,
                tenant__is_active=True
            )
            tenant = domain.tenant
            
        except TenantDomain.DoesNotExist:
            # Tentar buscar por subdomínio
            if '.' in host:
                subdomain = host.split('.')[0]
                try:
                    tenant = Tenant.objects.get(
                        slug=subdomain,
                        is_active=True
                    )
                except Tenant.DoesNotExist:
                    tenant = None
            else:
                tenant = None
        
        # Cachear resultado por 5 minutos
        if tenant:
            cache.set(cache_key, tenant, 300)
        
        return tenant
    
    def _is_api_request(self, request):
        """
        Verifica se é uma requisição API
        """
        return (
            request.path.startswith('/api/') or
            request.content_type == 'application/json' or
            'application/json' in request.META.get('HTTP_ACCEPT', '')
        )


class TenantDatabaseMiddleware(MiddlewareMixin):
    """
    Middleware para configurar conexão com banco baseado no tenant
    (Para uso futuro com database routing por tenant)
    """
    
    def process_request(self, request):
        if hasattr(request, 'tenant'):
            # Configurar database routing se necessário
            # request.db_alias = f"tenant_{request.tenant.slug}"
            pass


class TenantSecurityMiddleware(MiddlewareMixin):
    """
    Middleware de segurança específico para tenants
    """
    
    def process_request(self, request):
        if hasattr(request, 'tenant'):
            tenant = request.tenant
            
            # Verificar configurações de segurança do tenant
            settings = getattr(tenant, 'settings', None)
            if settings:
                # Configurar timeout de sessão
                if hasattr(settings, 'session_timeout_minutes'):
                    request.session.set_expiry(settings.session_timeout_minutes * 60)
                
                # Verificar autenticação de dois fatores obrigatória
                if (settings.two_factor_required and 
                    request.user.is_authenticated and 
                    not getattr(request.user, 'has_2fa_enabled', False)):
                    
                    # Redirecionar para configuração 2FA se necessário
                    if not request.path.startswith('/auth/2fa/'):
                        return HttpResponseRedirect(reverse('setup_2fa'))


# Funções utilitárias para thread local storage
def set_current_tenant(tenant):
    """Define o tenant atual no thread local"""
    _thread_locals.tenant = tenant


def get_current_tenant():
    """Obtém o tenant atual do thread local"""
    return getattr(_thread_locals, 'tenant', None)


def clear_current_tenant():
    """Limpa o tenant atual do thread local"""
    if hasattr(_thread_locals, 'tenant'):
        del _thread_locals.tenant


# Decorator para views que requerem tenant
def tenant_required(view_func):
    """
    Decorator que garante que uma view tem acesso ao tenant
    """
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'tenant'):
            raise Http404("Tenant required")
        return view_func(request, *args, **kwargs)
    return wrapper


# Context processor para templates
def tenant_context(request):
    """
    Context processor que adiciona informações do tenant aos templates
    """
    if hasattr(request, 'tenant'):
        return {
            'tenant': request.tenant,
            'tenant_context': getattr(request, 'tenant_context', {}),
        }
    return {}


class TenantCacheMiddleware(MiddlewareMixin):
    """
    Middleware para cache isolado por tenant
    """
    
    def process_request(self, request):
        if hasattr(request, 'tenant'):
            # Adicionar prefixo do tenant nas chaves de cache
            request.cache_prefix = f"tenant_{request.tenant.slug}"
    
    def process_response(self, request, response):
        if hasattr(request, 'cache_prefix'):
            # Configurar headers de cache específicos do tenant
            if response.get('Cache-Control'):
                response['Cache-Control'] = f"{response['Cache-Control']}, tenant={request.tenant.slug}"
        
        return response