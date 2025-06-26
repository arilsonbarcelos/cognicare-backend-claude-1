# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Modelo de usuário customizado para multi-tenancy
    """
    USER_TYPE_CHOICES = [
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('therapist', 'Terapeuta'),
        ('receptionist', 'Recepcionista'),
        ('parent', 'Responsável'),
        ('superadmin', 'Super Administrador'),
    ]
    
    SPECIALITY_CHOICES = [
        ('psychology', 'Psicologia'),
        ('speech_therapy', 'Fonoaudiologia'),
        ('occupational_therapy', 'Terapia Ocupacional'),
        ('physiotherapy', 'Fisioterapia'),
        ('pedagogy', 'Pedagogia'),
        ('psychopedagogy', 'Psicopedagogia'),
        ('nutrition', 'Nutrição'),
        ('psychiatry', 'Psiquiatria'),
        ('neurology', 'Neurologia'),
        ('other', 'Outro'),
    ]
    
    # Informações Básicas
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, verbose_name='Tipo de Usuário')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    cpf = models.CharField(
        max_length=14, 
        blank=True, 
        null=True, 
        unique=True,
        validators=[RegexValidator(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', 'CPF deve estar no formato XXX.XXX.XXX-XX')],
        verbose_name='CPF'
    )
    
    # Informações Profissionais (para terapeutas)
    speciality = models.CharField(
        max_length=30, 
        choices=SPECIALITY_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='Especialidade'
    )
    council_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Número do Conselho')
    council_state = models.CharField(max_length=2, blank=True, null=True, verbose_name='Estado do Conselho')
    
    # Endereço
    address = models.CharField(max_length=300, blank=True, null=True, verbose_name='Endereço')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cidade')
    state = models.CharField(max_length=2, blank=True, null=True, verbose_name='Estado')
    zipcode = models.CharField(max_length=10, blank=True, null=True, verbose_name='CEP')
    
    # Configurações de Trabalho
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name='Valor por Hora'
    )
    work_days = models.JSONField(
        default=list, 
        blank=True,
        help_text='Lista dos dias da semana que trabalha (0=Segunda, 6=Domingo)',
        verbose_name='Dias de Trabalho'
    )
    work_start_time = models.TimeField(blank=True, null=True, verbose_name='Horário de Início')
    work_end_time = models.TimeField(blank=True, null=True, verbose_name='Horário de Fim')
    
    # Configurações
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True, verbose_name='Foto')
    bio = models.TextField(blank=True, null=True, verbose_name='Biografia')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Datas
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    last_login_at = models.DateTimeField(blank=True, null=True, verbose_name='Último Login')
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        permissions = [
            ("can_manage_clinic", "Pode gerenciar clínica"),
            ("can_view_reports", "Pode visualizar relatórios"),
            ("can_manage_financials", "Pode gerenciar financeiro"),
            ("can_manage_schedules", "Pode gerenciar agendamentos"),
            ("can_access_medical_records", "Pode acessar prontuários"),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def is_therapist(self):
        return self.user_type == 'therapist'
    
    def is_admin_or_manager(self):
        return self.user_type in ['admin', 'manager', 'superadmin']
    
    def can_access_patient(self, patient):
        """
        Verifica se o usuário pode acessar um paciente específico
        """
        if self.is_admin_or_manager():
            return True
        
        if self.user_type == 'therapist':
            return patient.therapists.filter(id=self.id).exists()
        
        if self.user_type == 'parent':
            return patient.parents.filter(id=self.id).exists()
        
        return False


class UserTenantAssociation(models.Model):
    """
    Associação entre usuários e tenants
    Permite que um usuário trabalhe em múltiplas clínicas
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_associations')
    tenant_schema = models.CharField(max_length=100, verbose_name='Schema do Tenant')
    tenant_name = models.CharField(max_length=200, verbose_name='Nome da Clínica')