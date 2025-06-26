# apps/patients/models.py
from django.db import models
from django.core.validators import RegexValidator
from apps.users.models import User


class Patient(models.Model):
    """
    Modelo principal para pacientes neuroatípicos
    """
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
        ('N', 'Não informado'),
    ]
    
    DIAGNOSIS_CHOICES = [
        ('autism', 'Transtorno do Espectro Autista (TEA)'),
        ('adhd', 'Transtorno do Déficit de Atenção com Hiperatividade (TDAH)'),
        ('asperger', 'Síndrome de Asperger'),
        ('intellectual_disability', 'Deficiência Intelectual'),
        ('learning_disability', 'Dificuldades de Aprendizagem'),
        ('down_syndrome', 'Síndrome de Down'),
        ('cerebral_palsy', 'Paralisia Cerebral'),
        ('sensory_processing', 'Transtorno do Processamento Sensorial'),
        ('speech_delay', 'Atraso na Fala'),
        ('other', 'Outro'),
    ]
    
    SEVERITY_CHOICES = [
        ('mild', 'Leve'),
        ('moderate', 'Moderado'),
        ('severe', 'Severo'),
        ('not_applicable', 'Não se aplica'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('on_hold', 'Suspenso'),
        ('discharged', 'Alta'),
    ]
    
    # Informações Básicas
    name = models.CharField(max_length=200, verbose_name='Nome Completo')
    birth_date = models.DateField(verbose_name='Data de Nascimento')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='Gênero')
    cpf = models.CharField(
        max_length=14, 
        blank=True, 
        null=True,
        validators=[RegexValidator(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', 'CPF deve estar no formato XXX.XXX.XXX-XX')],
        verbose_name='CPF'
    )
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name='RG')
    
    # Endereço
    address = models.CharField(max_length=300, blank=True, null=True, verbose_name='Endereço')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cidade')
    state = models.CharField(max_length=2, blank=True, null=True, verbose_name='Estado')
    zipcode = models.CharField(max_length=10, blank=True, null=True, verbose_name='CEP')
    
    # Contato
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    emergency_contact = models.CharField(max_length=20, blank=True, null=True, verbose_name='Contato de Emergência')
    
    # Informações Clínicas
    primary_diagnosis = models.CharField(max_length=30, choices=DIAGNOSIS_CHOICES, verbose_name='Diagnóstico Principal')
    secondary_diagnosis = models.CharField(max_length=30, choices=DIAGNOSIS_CHOICES, blank=True, null=True, verbose_name='Diagnóstico Secundário')
    severity_level = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='not_applicable', verbose_name='Nível de Severidade')
    diagnosis_date = models.DateField(blank=True, null=True, verbose_name='Data do Diagnóstico')
    
    # Status e Tratamento
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Status')
    treatment_start_date = models.DateField(blank=True, null=True, verbose_name='Início do Tratamento')
    treatment_end_date = models.DateField(blank=True, null=True, verbose_name='Fim do Tratamento')
    
    # Informações Adicionais
    medical_history = models.TextField(blank=True, null=True, verbose_name='Histórico Médico')
    medications = models.TextField(blank=True, null=True, verbose_name='Medicações')
    allergies = models.TextField(blank=True, null=True, verbose_name='Alergias')
    special_needs = models.TextField(blank=True, null=True, verbose_name='Necessidades Especiais')
    
    # Relacionamentos
    therapists = models.ManyToManyField(
        User, 
        limit_choices_to={'user_type': 'therapist'}, 
        related_name='patients',
        blank=True,
        verbose_name='Terapeutas'
    )
    parents = models.ManyToManyField(
        User, 
        limit_choices_to={'user_type': 'parent'}, 
        related_name='children',
        blank=True,
        verbose_name='Responsáveis'
    )
    
    # Arquivos
    photo = models.ImageField(upload_to='patients/photos/', blank=True, null=True, verbose_name='Foto')
    
    # Datas
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def age(self):
        """Calcula a idade do paciente"""
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    def get_primary_therapist(self):
        """Retorna o terapeuta principal (primeiro cadastrado)"""
        return self.therapists.first()
    
    def get_active_treatment_plan(self):
        """Retorna o plano terapêutico ativo"""
        return self.treatment_plans.filter(is_active=True).first()


class PatientDocument(models.Model):
    """
    Documentos do paciente (laudos, relatórios, etc.)
    """
    DOCUMENT_TYPE_CHOICES = [
        ('medical_report', 'Laudo Médico'),
        ('psychological_report', 'Relatório Psicológico'),
        ('therapy_report', 'Relatório de Terapia'),
        ('school_report', 'Relatório Escolar'),
        ('assessment', 'Avaliação'),
        ('prescription', 'Prescrição'),
        ('insurance_form', 'Formulário de Convênio'),
        ('consent_form', 'Termo de Consentimento'),
        ('other', 'Outro'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200, verbose_name='Título')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES, verbose_name='Tipo de Documento')
    file = models.FileField(upload_to='patients/documents/', verbose_name='Arquivo')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Enviado por')
    is_confidential = models.BooleanField(default=False, verbose_name='Confidencial')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Documento do Paciente'
        verbose_name_plural = 'Documentos dos Pacientes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.name} - {self.title}"


class TreatmentPlan(models.Model):
    """
    Plano terapêutico do paciente
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='treatment_plans')
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'therapist'})
    
    title = models.CharField(max_length=200, verbose_name='Título do Plano')
    description = models.TextField(verbose_name='Descrição')
    
    # Objetivos
    short_term_goals = models.TextField(verbose_name='Objetivos de Curto Prazo')
    long_term_goals = models.TextField(verbose_name='Objetivos de Longo Prazo')
    
    # Período
    start_date = models.DateField(verbose_name='Data de Início')
    end_date = models.DateField(verbose_name='Data de Fim')
    
    # Frequência
    sessions_per_week = models.IntegerField(default=1, verbose_name='Sessões por Semana')
    session_duration = models.IntegerField(default=60, verbose_name='Duração da Sessão (min)')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    # Datas
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Plano Terapêutico'
        verbose_name_plural = 'Planos Terapêuticos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.name} - {self.title}"


class TreatmentGoal(models.Model):
    """
    Metas específicas do plano terapêutico
    """
    GOAL_TYPE_CHOICES = [
        ('communication', 'Comunicação'),
        ('social', 'Habilidades Sociais'),
        ('behavioral', 'Comportamental'),
        ('cognitive', 'Cognitivo'),
        ('motor', 'Motor'),
        ('sensory', 'Sensorial'),
        ('academic', 'Acadêmico'),
        ('daily_living', 'Vida Diária'),
        ('other', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', 'Não Iniciado'),
        ('in_progress', 'Em Progresso'),
        ('achieved', 'Alcançado'),
        ('discontinue