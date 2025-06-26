# apps/core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
import uuid


class TimestampedModel(models.Model):
    """
    Modelo abstrato que adiciona campos de timestamp para todos os modelos
    """
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Modelo abstrato que adiciona UUID como chave primária
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Modelo abstrato para soft delete
    """
    is_active = models.BooleanField(_('Ativo'), default=True)
    deleted_at = models.DateTimeField(_('Deletado em'), null=True, blank=True)
    
    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimestampedModel, SoftDeleteModel):
    """
    Modelo base que combina UUID, timestamps e soft delete
    """
    class Meta:
        abstract = True


class TenantAwareModel(BaseModel):
    """
    Modelo base para todos os modelos que devem ser isolados por tenant
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        db_index=True
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['tenant', 'is_active']),
        ]


class Address(BaseModel):
    """
    Modelo para endereços reutilizável
    """
    street = models.CharField(_('Rua'), max_length=255)
    number = models.CharField(_('Número'), max_length=20)
    complement = models.CharField(_('Complemento'), max_length=100, blank=True)
    neighborhood = models.CharField(_('Bairro'), max_length=100)
    city = models.CharField(_('Cidade'), max_length=100)
    state = models.CharField(_('Estado'), max_length=2)
    zip_code = models.CharField(
        _('CEP'),
        max_length=10,
        validators=[RegexValidator(regex=r'^\d{5}-?\d{3}$', message='CEP inválido')]
    )
    country = models.CharField(_('País'), max_length=50, default='Brasil')
    
    class Meta:
        verbose_name = _('Endereço')
        verbose_name_plural = _('Endereços')
    
    def __str__(self):
        return f"{self.street}, {self.number} - {self.city}/{self.state}"


class Phone(BaseModel):
    """
    Modelo para telefones reutilizável
    """
    PHONE_TYPES = [
        ('mobile', _('Celular')),
        ('home', _('Residencial')),
        ('work', _('Comercial')),
        ('emergency', _('Emergência')),
    ]
    
    number = models.CharField(
        _('Número'),
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
            message='Formato: (11) 99999-9999'
        )]
    )
    type = models.CharField(_('Tipo'), max_length=20, choices=PHONE_TYPES)
    is_primary = models.BooleanField(_('Principal'), default=False)
    is_whatsapp = models.BooleanField(_('WhatsApp'), default=False)
    
    class Meta:
        verbose_name = _('Telefone')
        verbose_name_plural = _('Telefones')
    
    def __str__(self):
        return f"{self.number} ({self.get_type_display()})"


class Document(BaseModel):
    """
    Modelo para documentos reutilizável
    """
    DOCUMENT_TYPES = [
        ('cpf', _('CPF')),
        ('rg', _('RG')),
        ('cnpj', _('CNPJ')),
        ('passport', _('Passaporte')),
        ('driver_license', _('CNH')),
        ('birth_certificate', _('Certidão de Nascimento')),
        ('other', _('Outro')),
    ]
    
    type = models.CharField(_('Tipo'), max_length=20, choices=DOCUMENT_TYPES)
    number = models.CharField(_('Número'), max_length=50)
    issuing_agency = models.CharField(_('Órgão Emissor'), max_length=50, blank=True)
    issue_date = models.DateField(_('Data de Emissão'), null=True, blank=True)
    expiry_date = models.DateField(_('Data de Validade'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Documento')
        verbose_name_plural = _('Documentos')
        unique_together = ['type', 'number']
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.number}"


class FileUpload(BaseModel):
    """
    Modelo base para uploads de arquivos
    """
    file = models.FileField(_('Arquivo'), upload_to='uploads/%Y/%m/%d/')
    original_name = models.CharField(_('Nome Original'), max_length=255)
    file_size = models.PositiveIntegerField(_('Tamanho do Arquivo'))
    content_type = models.CharField(_('Tipo de Conteúdo'), max_length=100)
    description = models.TextField(_('Descrição'), blank=True)
    
    class Meta:
        verbose_name = _('Upload de Arquivo')
        verbose_name_plural = _('Uploads de Arquivos')
    
    def __str__(self):
        return self.original_name


class Notification(TenantAwareModel):
    """
    Sistema de notificações
    """
    NOTIFICATION_TYPES = [
        ('info', _('Informação')),
        ('success', _('Sucesso')),
        ('warning', _('Aviso')),
        ('error', _('Erro')),
    ]
    
    NOTIFICATION_CHANNELS = [
        ('system', _('Sistema')),
        ('email', _('E-mail')),
        ('sms', _('SMS')),
        ('push', _('Push')),
    ]
    
    recipient = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(_('Título'), max_length=255)
    message = models.TextField(_('Mensagem'))
    type = models.CharField(_('Tipo'), max_length=20, choices=NOTIFICATION_TYPES)
    channel = models.CharField(_('Canal'), max_length=20, choices=NOTIFICATION_CHANNELS)
    is_read = models.BooleanField(_('Lida'), default=False)
    read_at = models.DateTimeField(_('Lida em'), null=True, blank=True)
    scheduled_for = models.DateTimeField(_('Agendada para'), null=True, blank=True)
    sent_at = models.DateTimeField(_('Enviada em'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Notificação')
        verbose_name_plural = _('Notificações')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['tenant', 'scheduled_for']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient}"


class SystemLog(BaseModel):
    """
    Logs do sistema para auditoria
    """
    LOG_LEVELS = [
        ('debug', _('Debug')),
        ('info', _('Info')),
        ('warning', _('Warning')),
        ('error', _('Error')),
        ('critical', _('Critical')),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='system_logs'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs'
    )
    level = models.CharField(_('Nível'), max_length=20, choices=LOG_LEVELS)
    action = models.CharField(_('Ação'), max_length=100)
    description = models.TextField(_('Descrição'))
    ip_address = models.GenericIPAddressField(_('IP'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    extra_data = models.JSONField(_('Dados Extras'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Log do Sistema')
        verbose_name_plural = _('Logs do Sistema')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'level', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.level.upper()} - {self.action} - {self.created_at}"


class Configuration(TenantAwareModel):
    """
    Configurações do sistema por tenant
    """
    key = models.CharField(_('Chave'), max_length=100)
    value = models.TextField(_('Valor'))
    description = models.TextField(_('Descrição'), blank=True)
    is_encrypted = models.BooleanField(_('Criptografado'), default=False)
    
    class Meta:
        verbose_name = _('Configuração')
        verbose_name_plural = _('Configurações')
        unique_together = ['tenant', 'key']
    
    def __str__(self):
        return f"{self.tenant} - {self.key}"