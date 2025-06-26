#!/bin/bash

# Nome da pasta raiz do projeto
PROJECT_ROOT="cognicare-backend"

echo "Criando a estrutura de pastas e arquivos para o projeto '$PROJECT_ROOT'..."

# Cria a pasta raiz e entra nela
mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT" || { echo "Falha ao entrar na pasta $PROJECT_ROOT. Abortando."; exit 1; }

# Criação das pastas e arquivos
# A ordem é importante para garantir que as pastas pai existam antes dos arquivos ou subpastas.

# Arquivos na raiz
touch manage.py
touch .env.example
touch .gitignore
touch .pre-commit-config.yaml
touch pyproject.toml
touch pytest.ini
touch Makefile
touch README.md

# requirements
mkdir -p requirements
touch requirements/base.txt
touch requirements/development.txt
touch requirements/production.txt
touch requirements/testing.txt

# config
mkdir -p config
touch config/__init__.py
mkdir -p config/settings
touch config/settings/__init__.py
touch config/settings/base.py
touch config/settings/development.py
touch config/settings/production.py
touch config/settings/testing.py
touch config/urls.py
touch config/wsgi.py
touch config/asgi.py

# apps
mkdir -p apps
touch apps/__init__.py

# apps/core
mkdir -p apps/core
touch apps/core/__init__.py
touch apps/core/models.py
touch apps/core/views.py
touch apps/core/urls.py
touch apps/core/admin.py
touch apps/core/apps.py
touch apps/core/managers.py
touch apps/core/mixins.py
touch apps/core/permissions.py
touch apps/core/serializers.py
touch apps/core/exceptions.py
mkdir -p apps/core/migrations

# apps/tenants
mkdir -p apps/tenants
touch apps/tenants/__init__.py
touch apps/tenants/models.py
touch apps/tenants/views.py
touch apps/tenants/urls.py
touch apps/tenants/admin.py
touch apps/tenants/apps.py
touch apps/tenants/middleware.py
touch apps/tenants/managers.py
touch apps/tenants/serializers.py
touch apps/tenants/utils.py
mkdir -p apps/tenants/migrations

# apps/users
mkdir -p apps/users
touch apps/users/__init__.py
touch apps/users/models.py
touch apps/users/views.py
touch apps/users/urls.py
touch apps/users/admin.py
touch apps/users/apps.py
touch apps/users/managers.py
touch apps/users/serializers.py
touch apps/users/permissions.py
touch apps/users/signals.py
mkdir -p apps/users/migrations

# apps/patients
mkdir -p apps/patients
touch apps/patients/__init__.py
touch apps/patients/models.py
touch apps/patients/views.py
touch apps/patients/urls.py
touch apps/patients/admin.py
touch apps/patients/apps.py
touch apps/patients/serializers.py
touch apps/patients/filters.py
touch apps/patients/forms.py
mkdir -p apps/patients/migrations

# apps/professionals
mkdir -p apps/professionals
touch apps/professionals/__init__.py
touch apps/professionals/models.py
touch apps/professionals/views.py
touch apps/professionals/urls.py
touch apps/professionals/admin.py
touch apps/professionals/apps.py
touch apps/professionals/serializers.py
touch apps/professionals/permissions.py
mkdir -p apps/professionals/migrations

# apps/scheduling
mkdir -p apps/scheduling
touch apps/scheduling/__init__.py
touch apps/scheduling/models.py
touch apps/scheduling/views.py
touch apps/scheduling/urls.py
touch apps/scheduling/admin.py
touch apps/scheduling/apps.py
touch apps/scheduling/serializers.py
touch apps/scheduling/services.py
touch apps/scheduling/tasks.py
touch apps/scheduling/utils.py
mkdir -p apps/scheduling/migrations

# apps/medical_records
mkdir -p apps/medical_records
touch apps/medical_records/__init__.py
touch apps/medical_records/models.py
touch apps/medical_records/views.py
touch apps/medical_records/urls.py
touch apps/medical_records/admin.py
touch apps/medical_records/apps.py
touch apps/medical_records/serializers.py
touch apps/medical_records/forms.py
touch apps/medical_records/services.py
mkdir -p apps/medical_records/migrations

# apps/family_portal
mkdir -p apps/family_portal
touch apps/family_portal/__init__.py
touch apps/family_portal/models.py
touch apps/family_portal/views.py
touch apps/family_portal/urls.py
touch apps/family_portal/admin.py
touch apps/family_portal/apps.py
touch apps/family_portal/serializers.py
touch apps/family_portal/permissions.py
mkdir -p apps/family_portal/migrations

# apps/financial
mkdir -p apps/financial
touch apps/financial/__init__.py
touch apps/financial/models.py
touch apps/financial/views.py
touch apps/financial/urls.py
touch apps/financial/admin.py
touch apps/financial/apps.py
touch apps/financial/serializers.py
touch apps/financial/services.py
touch apps/financial/tasks.py
touch apps/financial/utils.py
mkdir -p apps/financial/migrations

# apps/clinic_management
mkdir -p apps/clinic_management
touch apps/clinic_management/__init__.py
touch apps/clinic_management/models.py
touch apps/clinic_management/views.py
touch apps/clinic_management/urls.py
touch apps/clinic_management/admin.py
touch apps/clinic_management/apps.py
touch apps/clinic_management/serializers.py
touch apps/clinic_management/reports.py
touch apps/clinic_management/analytics.py
mkdir -p apps/clinic_management/migrations

# apps/communication
mkdir -p apps/communication
touch apps/communication/__init__.py
touch apps/communication/models.py
touch apps/communication/views.py
touch apps/communication/urls.py
touch apps/communication/admin.py
touch apps/communication/apps.py
touch apps/communication/serializers.py
touch apps/communication/services.py
touch apps/communication/tasks.py
touch apps/communication/notifications.py
mkdir -p apps/communication/migrations

# apps/api
mkdir -p apps/api
touch apps/api/__init__.py
mkdir -p apps/api/v1
touch apps/api/v1/__init__.py
touch apps/api/v1/urls.py
touch apps/api/v1/views.py
touch apps/api/v1/serializers.py
touch apps/api/v1/permissions.py
mkdir -p apps/api/v2
touch apps/api/v2/__init__.py
touch apps/api/v2/urls.py
touch apps/api/v2/views.py
touch apps/api/v2/serializers.py
touch apps/api/v2/permissions.py

# shared
mkdir -p shared
touch shared/__init__.py

# shared/utils
mkdir -p shared/utils
touch shared/utils/__init__.py
touch shared/utils/helpers.py
touch shared/utils/validators.py
touch shared/utils/decorators.py
touch shared/utils/mixins.py
touch shared/utils/constants.py

# shared/middleware
mkdir -p shared/middleware
touch shared/middleware/__init__.py
touch shared/middleware/tenant.py
touch shared/middleware/security.py
touch shared/middleware/logging.py

# shared/exceptions
mkdir -p shared/exceptions
touch shared/exceptions/__init__.py
touch shared/exceptions/custom.py
touch shared/exceptions/handlers.py

# shared/services
mkdir -p shared/services
touch shared/services/__init__.py
touch shared/services/email.py
touch shared/services/sms.py
touch shared/services/storage.py
touch shared/services/payment.py
touch shared/services/pdf_generator.py

# shared/tasks
mkdir -p shared/tasks
touch shared/tasks/__init__.py
touch shared/tasks/celery.py
touch shared/tasks/email_tasks.py
touch shared/tasks/report_tasks.py
touch shared/tasks/cleanup_tasks.py

# templates
mkdir -p templates
mkdir -p templates/base
touch templates/base/base.html
touch templates/base/header.html
touch templates/base/footer.html
touch templates/base/sidebar.html

# templates/auth
mkdir -p templates/auth
touch templates/auth/login.html
touch templates/auth/register.html
touch templates/auth/password_reset.html

# templates/dashboard
mkdir -p templates/dashboard
touch templates/dashboard/index.html
mkdir -p templates/dashboard/widgets

# templates/patients
mkdir -p templates/patients
touch templates/patients/list.html
touch templates/patients/detail.html
touch templates/patients/form.html

# templates/scheduling
mkdir -p templates/scheduling
touch templates/scheduling/calendar.html
touch templates/scheduling/appointment_form.html

# templates/family_portal
mkdir -p templates/family_portal
touch templates/family_portal/dashboard.html
touch templates/family_portal/progress.html

# templates/reports
mkdir -p templates/reports
touch templates/reports/base_report.html
touch templates/reports/financial_report.html

# templates/email
mkdir -p templates/email
touch templates/email/base_email.html
touch templates/email/appointment_reminder.html
touch templates/email/welcome.html

# static
mkdir -p static

# static/css
mkdir -p static/css
touch static/css/base.css
touch static/css/dashboard.css
touch static/css/forms.css
touch static/css/tenant_custom.css

# static/js
mkdir -p static/js
touch static/js/main.js
touch static/js/calendar.js
touch static/js/charts.js
touch static/js/forms.js
touch static/js/notifications.js

# static/img
mkdir -p static/img
mkdir -p static/img/logos
mkdir -p static/img/icons
mkdir -p static/img/pictograms

# static/vendor
mkdir -p static/vendor
mkdir -p static/vendor/bootstrap
mkdir -p static/vendor/jquery
mkdir -p static/vendor/chart.js

# media
mkdir -p media
mkdir -p media/tenant_files/{tenant_id}/logos
mkdir -p media/tenant_files/{tenant_id}/documents
mkdir -p media/tenant_files/{tenant_id}/patient_files
mkdir -p media/tenant_files/{tenant_id}/reports
mkdir -p media/system/default_logos
mkdir -p media/system/pictograms

# tests
mkdir -p tests
touch tests/__init__.py
touch tests/conftest.py

# tests/factories
mkdir -p tests/factories
touch tests/factories/__init__.py
touch tests/factories/tenant_factory.py
touch tests/factories/user_factory.py
touch tests/factories/patient_factory.py
touch tests/factories/appointment_factory.py

# tests/integration
mkdir -p tests/integration
touch tests/integration/__init__.py
touch tests/integration/test_tenant_isolation.py
touch tests/integration/test_api_endpoints.py
touch tests/integration/test_workflows.py

# tests/unit
mkdir -p tests/unit
touch tests/unit/__init__.py
mkdir -p tests/unit/test_models
mkdir -p tests/unit/test_views
mkdir -p tests/unit/test_services
mkdir -p tests/unit/test_utils

# tests/fixtures
mkdir -p tests/fixtures
touch tests/fixtures/tenants.json
touch tests/fixtures/users.json
touch tests/fixtures/sample_data.json

# docs
mkdir -p docs
touch docs/README.md
touch docs/API.md
touch docs/DEPLOYMENT.md
touch docs/ARCHITECTURE.md
touch docs/MULTI_TENANT.md
touch docs/DEVELOPMENT.md

# scripts
mkdir -p scripts
touch scripts/setup_dev.sh
touch scripts/deploy.sh
touch scripts/backup_db.sh
touch scripts/create_tenant.py
touch scripts/migrate_tenant.py

# docker
mkdir -p docker
touch docker/Dockerfile
touch docker/docker-compose.yml
touch docker/docker-compose.prod.yml
touch docker/nginx.conf

# logs
mkdir -p logs
touch logs/django.log
touch logs/celery.log
touch logs/tenant_activity.log

# locale
mkdir -p locale/pt_BR/LC_MESSAGES
touch locale/pt_BR/LC_MESSAGES/django.po
touch locale/pt_BR/LC_MESSAGES/django.mo
mkdir -p locale/en/LC_MESSAGES
touch locale/en/LC_MESSAGES/django.po
touch locale/en/LC_MESSAGES/django.mo

echo "Estrutura de pastas e arquivos criada com sucesso em '$PROJECT_ROOT'!"

# Retorna para o diretório original
cd - > /dev/null
