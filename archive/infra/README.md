# Cloud & Enterprise Infrastructure Archive

The following enterprise cloud orchestration and telemetry files were moved here as part of tailoring the repository for **Syntropic Sense** local in-home ambient sensing:

- `deploy.sh`: Cloud deployment script for AWS EKS, Terraform, Helm, and Kubernetes
- `scripts-gcp/`: Google Cloud Platform cluster and remote training VM provisioning
- `scripts-gcloud-train.sh`: Remote cloud model training orchestration
- `logging/`: Enterprise Fluentd cluster logging configuration
- `monitoring/`: Prometheus and Grafana alerting and monitoring stack
- `otel-collector.yaml`: OpenTelemetry enterprise collector configuration
- `otel-compose.yml`: Docker compose configuration for OpenTelemetry

The in-home hub operates 100% on-premises via a lightweight, zero-cloud Docker Compose runtime (`docker/docker-compose.yml`) and local SQLite persistence.
