# Лекция 21. Infrastructure as Code (IaC) и автоматизация

## Цель
Понять, как описывать инфраструктуру в виде кода: декларативная модель, идемпотентность, повторяемость, контроль изменений через Git, автоматическое применение через CI/CD и GitOps. Рассмотрим Terraform (как де‑факто стандарт), упомянем Ansible, CloudFormation, Pulumi; разберём стейт, модули, бэкенды, drift detection, Policy as Code (OPA/Sentinel), управление секретами (Vault/KMS), многоокружную стратегию, практикум.

## План
1. Зачем IaC: проблемы ручных настроек, скорость, воспроизводимость.
2. Декларативное vs императивное: Terraform vs Ansible.
3. Принципы: желаемое состояние, идемпотентность, идempotent apply, drift detection, атомарность.
4. Terraform основы: провайдеры, ресурсы, data sources, зависимости (graph).
5. Состояние (state): хранение, гонки, backend, locking.
6. Модули и реюз: интерфейсы (variables, outputs), version pinning.
7. Backends (local/S3/GCS/Azure Blob) + блокировка (DynamoDB/Consul).
8. Workspaces и окружения (dev/stage/prod) vs отдельные каталоги.
9. Policy as Code: OPA/Conftest, Sentinel, проверка перед apply.
10. Секреты: Vault, KMS, SOPS, не класть секреты в стейт.
11. GitOps для инфраструктуры: PR, review, план в комментарии, автоприменение.
12. Практикум: модуль деплоя приложения в Kubernetes.
13. Доп. материалы и вопросы.

---

## 1. Зачем IaC
Ручная настройка (клики в консоли) приводит к:
- "Works on my machine" — сложно воспроизвести.
- Отсутствие истории изменений.
- Ошибки из‑за человеческого фактора.
IaC = код → версионирование, тесты, review, автоматизация.

## 2. Декларативное vs Императивное
- Декларативное: описываем желаемое состояние (Terraform/CloudFormation) → движок решает как прийти.
- Императивное: последовательность шагов (Ansible, bash). Можно комбинировать: Terraform + Ansible (инфраструктура + конфигурация).

```plaintext
Terraform: resource "aws_instance" "web" {...}
Ansible: - name: Install nginx
					apt: name=nginx state=latest
```

## 3. Ключевые принципы IaC
1. Желательное состояние (desired state).
2. Идемпотентность: повторный `apply` не меняет ничего при неизменном коде.
3. Drift Detection: обнаружение расхождения стейта с реальностью (изменения вручную). Команда `terraform plan` показывает дрейф.
4. Мин. доступ: изменения через CI, а не локально (audit).
5. Малые итерации: маленькие PR → проще ревью.

## 4. Terraform основы
### Структура файлов
`providers.tf`, `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`.

### Провайдер
```hcl
terraform {
	required_providers {
		aws = {
			source  = "hashicorp/aws"
			version = "~> 5.0"
		}
	}
	required_version = ">= 1.6.0"
}

provider "aws" {
	region = var.region
}
```

### Ресурс
```hcl
resource "aws_s3_bucket" "logs" {
	bucket = "my-logs-${var.environment}"
	tags = { env = var.environment }
}
```

### Data source
```hcl
data "aws_iam_policy_document" "readonly" {
	statement {
		actions   = ["s3:GetObject"]
		resources = ["${aws_s3_bucket.logs.arn}/*"]
	}
}
```

### Переменные
```hcl
variable "environment" { type = string }
variable "region" { type = string default = "eu-central-1" }
```

### Выходы
```hcl
output "bucket_name" { value = aws_s3_bucket.logs.bucket }
```

### Граф зависимостей
Terraform строит DAG: ресурсы создаются параллельно, если нет зависимостей; уничтожение в обратном порядке.

## 5. State (состояние)
Хранит текущее соответствие ресурсов → ID, атрибуты. Нужен для планирования (diff).

Проблемы:
- Локальный `terraform.tfstate` → риск потери, гонок.
- Секреты могут попасть в стейт (например, сгенерированные пароли) → нужно защищать.

### Backend
```hcl
terraform {
	backend "s3" {
		bucket         = "iac-states"
		key            = "prod/network/terraform.tfstate"
		region         = "eu-central-1"
		dynamodb_table = "terraform-locks" # для блокировки
		encrypt        = true
	}
}
```
Locking предотвращает одновременный apply.

### Remote state data
Можно читать выходы одного стейта в другом (разделение на слои: network, services).

## 6. Модули
Модуль = директория с набором ресурсов + интерфейс (variables/outputs).

Использование:
```hcl
module "app" {
	source       = "git::https://github.com/org/tf-modules.git//app?ref=v1.2.3"
	name         = "frontend"
	image        = var.image
	replicas     = 3
	cpu_request  = "250m"
	memory_limit = "512Mi"
}
```

### Best practices
- Версионирование (`?ref=tag`).
- Документация (`README.md` + пример `examples/`).
- Минимум обязательных переменных.
- Валидация через `variable { validation { condition ... } }`.

Пример валидации переменной:
```hcl
variable "environment" {
	type = string
	validation {
		condition     = contains(["dev","stage","prod"], var.environment)
		error_message = "environment must be dev|stage|prod"
	}
}
```

## 7. Workspaces и окружения
`terraform workspace` позволяет переключать логический набор состояния (dev/stage/prod). Альтернатива — отдельные каталоги/репозитории.

Рекомендация: для сложных систем лучше отдельные папки/бэкенды (явная изоляция), а workspace — для простых вариаций.

## 8. Drift detection
`terraform plan` показывает расхождения. Автоматизация: периодический план в CI → уведомление, если есть неожиданные изменения.

## 9. Policy as Code
### OPA/Conftest
Пишем правила на Rego, проверяем Terraform план до применения.

Пример правила (запрет открытых S3 bucket):
```rego
package terraform.security

deny[msg] {
	input.resource_changes[_].type == "aws_s3_bucket"
	some i
	input.resource_changes[i].change.after.acl == "public-read"
	msg = "S3 bucket should not be public-read"
}
```
Запуск: `conftest test plan.json` (где `plan.json` = `terraform show -json plan.out`).

### Sentinel (HashiCorp Cloud)
Привязка к Terraform Cloud workflows. Аналогично: политика перед apply.

## 10. Секреты
Проблема: нельзя хранить статические пароли/API ключи в коде или в открытом стейте.

Решения:
- HashiCorp Vault: динамические секреты (lease + revoke), интеграция с Terraform.
- KMS (AWS/GCP): шифрование значений, SOPS (git‑хранение шифрованных файлов).
- Использовать `sensitive = true` в outputs.

Пример шифрования через SOPS (yaml файл с ключами). Terraform читает расшифрованный файл через внешнюю data source (скрипт).

## 11. GitOps для инфраструктуры
Workflow:
1. Разработчик делает PR с изменениями `.tf`.
2. CI запускает `terraform init` + `plan`; сохраняет артефакт.
3. CI публикует план как комментарий в PR (diff).
4. Reviewer одобряет → merge.
5. Post‑merge job выполняет `terraform apply` (используя сохранённый план для гарантии неизменности).

Преимущества: audit trail, обязательное ревью, автоматический drift detection.

## 12. Практикум: Kubernetes модуль
Задача: создать модуль деплоя приложения.

### Структура
```plaintext
modules/app/
	main.tf
	variables.tf
	outputs.tf
	README.md
```

### Пример main.tf
```hcl
resource "kubernetes_namespace" "app" {
	metadata { name = var.namespace }
}

resource "kubernetes_deployment" "app" {
	metadata { name = var.name namespace = var.namespace }
	spec {
		replicas = var.replicas
		selector { match_labels = { app = var.name } }
		template {
			metadata { labels = { app = var.name } }
			spec {
				container {
					image = var.image
					name  = var.name
					resources {
						limits = { cpu = var.cpu_limit, memory = var.memory_limit }
					}
					port { container_port = 8080 }
					env { name = "ENV" value = var.environment }
				}
			}
		}
	}
}

resource "kubernetes_service" "app" {
	metadata { name = var.name namespace = var.namespace }
	spec {
		selector = { app = var.name }
		port { port = 80 target_port = 8080 }
		type = "ClusterIP"
	}
}
```

### variables.tf (частично)
```hcl
variable "namespace" { type = string }
variable "name" { type = string }
variable "image" { type = string }
variable "replicas" { type = number default = 2 }
variable "cpu_limit" { type = string default = "500m" }
variable "memory_limit" { type = string default = "512Mi" }
variable "environment" { type = string default = "dev" }
```

### outputs.tf
```hcl
output "service_name" { value = kubernetes_service.app.metadata[0].name }
```

### Использование
```hcl
module "frontend" {
	source     = "./modules/app"
	namespace  = "frontend"
	name       = "web"
	image      = "myrepo/web:v1.0.0"
	replicas   = 3
	environment = "stage"
}
```

### Задание
1. Добавьте `HorizontalPodAutoscaler` (через ресурс или `kubernetes_manifest`).
2. Введите валидацию переменной `environment`.
3. Добавьте output с именем namespace.
4. Настройте backend S3 + DynamoDB lock (если доступен облачный аккаунт).
5. Реализуйте pipeline: `terraform fmt` → `validate` → `plan`.

## 13. Дополнительные инструменты
- Pulumi (IaC на настоящих языках: TS/Python/Go/C#).
- Ansible (конфигурация/пакеты внутри VM).
- CloudFormation (AWS‑native шаблоны JSON/YAML).
- Crossplane (Kubernetes CRD управляет облачными ресурсами).

## 14. Типичные ошибки и анти‑паттерны
1. Хранение секретов в открытом виде (пароли в `.tf`).
2. Смешивание окружений в одном стейте (dev/prod).
3. Слишком монолитные модули (трудно переиспользовать).
4. Отсутствие версионирования модулей → неожиданные изменения.
5. Ручные правки в консоли без последующего `plan` → дрейф.

## 15. Дополнительные материалы
- Terraform Docs: https://developer.hashicorp.com/terraform/docs
- Terraform Registry: https://registry.terraform.io/
- OPA / Conftest: https://www.openpolicyagent.org/
- Vault: https://www.vaultproject.io/
- GitOps Principles: https://www.gitops.tech/
- Pulumi: https://www.pulumi.com/

## 16. Вопросы для самопроверки
1. Чем декларативный подход отличается от императивного?
2. Что такое идемпотентность в контексте IaC?
3. Зачем нужен Terraform state и почему его нельзя просто удалить?
4. Как работает блокировка состояния при использовании S3 + DynamoDB?
5. Для чего нужны модули и какие best practices их проектирования?
6. Что такое drift и как его обнаружить?
7. В чём пользу Policy as Code и пример правила?
8. Почему нельзя хранить секреты в стейте? Как избежать?
9. Разница между workspace и отдельной директорией для окружений?
10. Что такое GitOps и как выглядит типичный workflow для Terraform?
11. Когда выбрать Ansible вместо Terraform?
12. Какие риски несёт удаление стейта вручную?
13. Для чего нужны outputs и remote state?
14. Зачем ограничивать список допустимых значений переменной (валидация)?
15. Какие преимущества даёт использование Pulumi?

---
**Итог:** IaC превращает инфраструктуру в предсказуемый, версионируемый и проверяемый артефакт. Правильное управление стейтом, использование модулей, политик и GitOps повышает надёжность и снижает операционные риски. Практикуйтесь на небольших модулях, постепенно добавляя сложность.
