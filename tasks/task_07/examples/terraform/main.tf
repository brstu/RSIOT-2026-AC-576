# Стенд «СмартДома» кодом — эталон варианта 0 (ЛР07).
# Работает и с Terraform, и с OpenTofu (единый HCL — лекция 21).
terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "kind-smartdom"
}

variable "namespace" {
  type    = string
  default = "smartdom"
}

variable "alert_threshold_c" {
  type    = number
  default = 60
}

resource "kubernetes_namespace" "stand" {
  metadata {
    name = var.namespace
    labels = {
      "org.bstu.course" = "RSIOT"
    }
  }
}

# Параметры стенда: их же читает приложение из infra/ (лаба 5)
resource "kubernetes_config_map" "stand_params" {
  metadata {
    name      = "stand-params"
    namespace = kubernetes_namespace.stand.metadata[0].name
  }
  data = {
    ALERT_THRESHOLD_C = tostring(var.alert_threshold_c)
    STAND_OWNER       = "variant-0"
  }
}

output "namespace" {
  value = kubernetes_namespace.stand.metadata[0].name
}
