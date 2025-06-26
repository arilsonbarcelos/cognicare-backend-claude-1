# apps/tenants/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, URLValidator
from django.contrib.postgres.fields import ArrayField
from apps.core.models import BaseModel, Address, Phone, Document
import uuid


class TenantManager(models.Manager):
    """
    Manager customizado para Tenants
    """
    def active(self):
        return self.filter(is_active=True, subscription_status='active')
    
    def by_domain(self, domain):
        return self.filter(domains__domain=domain, is_active=True).first()


class Tenant(BaseModel):
    """
    Modelo principal para multi-tenancy
    """
    SUBSCRIPTION_PLANS = [
        ('basic', _('Básico')),
        ('professional', _('Profissional')),
        ('enterprise', _('Enterprise')),
    ]
    
    SUBSCRIPTION_STATUS = [
        ('trial', _('Trial')),
        ('active', _('Ativo')),
        ('suspended', _('Suspenso')),
        ('cancelled', _('Cancelado')),
        ('expired', _('Expirado')),
    ]
    
    # Informações básicas
    name = models.CharField(_('Nome da Clínica'), max_length=255)
    slug = models.SlugField(_('Slug'), unique=True, max_length=100)
    description = models.TextField(_('Descrição'), blank=True)
    
    # Contato
    email = models.EmailField(_('E-mail Principal'))
    website = models.URLField(_('Website'), blank=True)
    
    # Configurações de assinatura
    subscription_plan = models.CharField(
        _('Plano de Assinatura'),
        max_length=20,
        choices=SUBSCRIPTION_PLANS,
        default='basic'
    )
    subscription_status = models.CharField(
        _('Status da Assinatura'),
        max_length=20,
        choices=SUBSCRIPTION_STATUS,
        default='trial'
    )
    subscription_start = models.DateTimeField(_('Início da Assinatura'), null=True, blank=True)
    subscription_end = models.DateTimeField(_('Fim da Assinatura'), null=True, blank=True)
    trial_end = models.DateTimeField(_('Fim do Trial'), null=True, blank=True)
    
    # Limites por plano
    max_users = models.PositiveIntegerField(_('Máximo de Usuários'), default=10)
    max_patients = models.PositiveIntegerField(_('Máximo de Pacientes'), default=100)
    max_storage_gb = models.PositiveIntegerField(_('Máximo de Storage (GB)'), default=5)
    
    # Customização
    logo = models.ImageField(_('Logo'), upload_to='tenant_logos/', blank=True)
    primary_color = models.CharField(
        _('Cor Primária'),
        max_length=7,
        default='#007bff',
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$')]
    )
    secondary_color = models.CharField(
        _('Cor Secundária'),
        max_length=7,
        default='#6c757d',
        validators=[RegexValidator(regex=r'^#[0-9A-Fa-f]{6}$')]
    )
    custom_css = models.TextField(_('CSS Customizado'), blank=True)
    
    # Configurações regionais
    timezone = models.CharField(_('Fuso Horário'), max_length=50, default='America/Sao_Paulo')
    language = models.CharField(_('Idioma'), max_length=10, default='pt-br')
    currency = models.CharField(_('Moeda'), max_length=3, default='BRL')
    
    # Configurações de funcionalidades
    enabled_modules = ArrayField(
        models.CharField(max_length=50),
        verbose_name=_('Módulos Habilitados'),
        default=list,
        blank=True,
        help_text=_('Lista de módulos habilitados para este tenant')
    )
    
    # Metadados
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tenants'
    )
    
    objects = TenantManager()
    
    class Meta:
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        ordering = ['name']
        indexes = [
            models.Index(fields=['subscription_status', 'is_active']),
            models.Index(fields=['subscription_end']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_trial(self):
        return self.subscription_status == 'trial'
    
    @property
    def is_subscription_active(self):
        return self.subscription_status == 'active'
    
    def get_primary_domain(self):
        return self.domains.filter(is_primary=True).first()
    
    def get_current_usage(self):
        """Retorna o uso atual de recursos"""
        from apps.users.models import User
        from apps.patients.models import Patient
        
        return {
            'users': User.objects.filter(tenant=self).count(),
            'patients': Patient.objects.filter(tenant=self).count(),
            'storage_gb': 0,  # TODO: Implementar cálculo de storage
        }
    
    def check_limits(self, resource_type, additional=1):
        """Verifica se está dentro dos limites"""
        usage = self.get_current_usage()
        current = usage.get(resource_type, 0)
        limit = getattr(self, f'max_{resource_type}', 0)
        
        return (current + additional) <= limit


class TenantDomain(BaseModel):
    """
    Domínios associados aos tenants
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='domains'
    )
    domain = models.CharField(_('Domínio'), max_length=255, unique=True)
    is_primary = models.BooleanField(_('Domínio Principal'), default=False)
    is_verified = models.BooleanField(_('Verificado'), default=False)
    ssl_enabled = models.BooleanField(_('SSL Habilitado'), default=True)
    
    class Meta:
        verbose_name = _('Domínio do Tenant')
        verbose_name_plural = _('Domínios dos Tenants')
        unique_together = ['tenant', 'domain']
    
    def __str__(self):
        return f"{self.domain} ({'Primary' if self.is_primary else 'Secondary'})"
    
    def save(self, *args, **kwargs):
        # Garante que apenas um domínio seja primário por tenant
        if self.is_primary:
            TenantDomain.objects.filter(
                tenant=self.tenant,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)


class TenantAddress(Address):
    """
    Endereços dos tenants
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    address_type = models.CharField(
        _('Tipo de Endereço'),
        max_length=20,
        choices=[
            ('main', _('Principal')),
            ('billing', _('Cobrança')),
            ('branch', _('Filial')),
        ],
        default='main'
    )
    
    class Meta:
        verbose_name = _('Endereço do Tenant')
        verbose_name_plural = _('Endereços dos Tenants')


class TenantPhone(Phone):
    """
    Telefones dos tenants
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='phones'
    )
    
    class Meta:
        verbose_name = _('Telefone do Tenant')
        verbose_name_plural = _('Telefones dos Tenants')


class TenantDocument(Document):
    """
    Documentos dos tenants (CNPJ, Inscrição Estadual, etc.)
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    class Meta:
        verbose_name = _('Documento do Tenant')
        verbose_name_plural = _('Documentos dos Tenants')


class TenantSettings(BaseModel):
    """
    Configurações específicas do tenant
    """
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Configurações de agendamento
    working_days = ArrayField(
        models.IntegerField(choices=[
            (0, _('Segunda-feira')),
            (1, _('Terça-feira')),
            (2, _('Quarta-feira')),
            (3, _('Quinta-feira')),
            (4, _('Sexta-feira')),
            (5, _('Sábado')),
            (6, _('Domingo')),
        ]),
        verbose_name=_('Dias de Funcionamento'),
        default=list,
        help_text=_('0=Segunda, 1=Terça, ..., 6=Domingo')
    )
    working_hours_start = models.TimeField(_('Horário de Início'), default='08:00')
    working_hours_end = models.TimeField(_('Horário de Fim'), default='18:00')
    appointment_duration = models.PositiveIntegerField(_('Duração Padrão da Sessão (min)'), default=50)
    advance_booking_days = models.PositiveIntegerField(_('Dias de Antecedência para Agendamento'), default=30)
    cancellation_hours = models.PositiveIntegerField(_('Horas de Antecedência para Cancelamento'), default=24)
    
    # Configurações de notificação
    email_notifications = models.BooleanField(_('Notificações por E-mail'), default=True)
    sms_notifications = models.BooleanField(_('Notificações por SMS'), default=False)
    reminder_hours_before = models.PositiveIntegerField(_('Lembrete (horas antes)'), default=24)
    
    # Configurações financeiras
    default_currency = models.CharField(_('Moeda Padrão'), max_length=3, default='BRL')
    payment_methods = ArrayField(
        models.CharField(max_length=20),
        verbose_name=_('Métodos de Pagamento'),
        default=list,
        blank=True
    )
    invoice_due_days = models.PositiveIntegerField(_('Prazo de Vencimento (dias)'), default=30)
    late_fee_percentage = models.DecimalField(_('Taxa de Atraso (%)'), max_digits=5, decimal_places=2, default=2.00)
    
    # Configurações de segurança
    password_min_length = models.PositiveIntegerField(_('Tamanho Mínimo da Senha'), default=8)
    session_timeout_minutes = models.PositiveIntegerField(_('Timeout da Sessão (min)'), default=480)
    max_login_attempts = models.PositiveIntegerField(_('Máximo de Tentativas de Login'), default=5)
    two_factor_required = models.BooleanField(_('Autenticação de Dois Fatores Obrigatória'), default=False)
    
    # Configurações de backup
    auto_backup = models.BooleanField(_('Backup Automático'), default=True)
    backup_frequency_days = models.PositiveIntegerField(_('Frequência de Backup (dias)'), default=7)
    backup_retention_days = models.PositiveIntegerField(_('Retenção de Backup (dias)'), default=90)
    
    class Meta:
        verbose_name = _('Configurações do Tenant')
        verbose_name_plural = _('Configurações dos Tenants')
    
    def __str__(self):
        return f"Configurações - {self.tenant.name}"


class TenantInvitation(BaseModel):
    """
    Convites para usuários ingressarem em um tenant
    """
    INVITATION_STATUS = [
        ('pending', _('Pendente')),    
        ('accepted', _('Aceito')),
        ('declined', _('Recusado')),
        ('expired', _('Expirado')),
    ]
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    email = models.EmailField(_('E-mail'))
    role = models.CharField(_('Função'), max_length=50)
    invited_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    token = models.UUIDField(_('Token'), default=uuid.uuid4, unique=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=INVITATION_STATUS,
        default='pending'
    )
    expires_at = models.DateTimeField(_('Expira em'))
    accepted_at = models.DateTimeField(_('Aceito em'), null=True, blank=True)
    accepted_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invitations'
    )
    message = models.TextField(_('Mensagem'), blank=True)
    
    class Meta:
        verbose_name = _('Convite')
        verbose_name_plural = _('Convites')
        unique_together = ['tenant', 'email', 'status']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Convite para {self.email} - {self.tenant.name}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def can_be_accepted(self):
        return self.status == 'pending' and not self.is_expired