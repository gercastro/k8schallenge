import subprocess
import time
import sys
import requests
import json
import os

NAMESPACE = "monitoring"
GRAFANA_ADMIN_USER = "admin"
GRAFANA_ADMIN_PASSWORD = "admin"
GRAFANA_INGRESS_HOST = "grafana.local"
PROMETHEUS_SVC_DNS = "http://prometheus-server.monitoring.svc.cluster.local"

def run(cmd):
    print(f"-> Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(result.returncode)
    return result.stdout

def wait_for_grafana():
    print("Esperando que Grafana esté lista en el cluster...")
    for _ in range(30):
        try:
            r = requests.get(f"http://{GRAFANA_INGRESS_HOST}/login", timeout=2)
            if r.status_code == 200:
                print("Grafana responde!")
                return
        except Exception:
            pass
        time.sleep(5)
    print("No se pudo acceder a Grafana en el Ingress. Revisá el despliegue.")
    sys.exit(1)

def create_grafana_datasource():
    print("Configurando DataSource de Prometheus en Grafana...")
    url = f"http://{GRAFANA_INGRESS_HOST}/api/datasources"
    headers = {"Content-Type": "application/json"}
    auth = (GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASSWORD)
    payload = {
        "name": "Prometheus",
        "type": "prometheus",
        "access": "proxy",
        "url": PROMETHEUS_SVC_DNS,
        "basicAuth": False,
        "isDefault": True,
    }
    r = requests.post(url, headers=headers, auth=auth, json=payload)
    if r.status_code in (200, 409):  # 409 = ya existe
        print("Datasource configurado.")
    else:
        print("Error al configurar el datasource:", r.text)
        sys.exit(1)

def import_grafana_dashboard(json_file):
    print(f"Importando dashboard {json_file} en Grafana...")
    url = f"http://{GRAFANA_INGRESS_HOST}/api/dashboards/import"
    headers = {"Content-Type": "application/json"}
    auth = (GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASSWORD)
    with open(json_file, "rb") as f:
        dash_json = json.loads(f.read().decode("utf-8"))
    payload = {
        "dashboard": dash_json,
        "overwrite": True,
        "folderId": 0,
        "inputs": [
            {
                "name": "DS__VICTORIAMETRICS-PROD-ALL",
                "type": "datasource",
                "pluginId": "prometheus",
                "value": "Prometheus"
            }
        ]
    }
    r = requests.post(url, headers=headers, auth=auth, json=payload)
    if r.status_code in (200, 201):
        print("Dashboard importado OK.")
    else:
        print("Error importando dashboard:", r.text)
        sys.exit(1)

def main():
    # 1. Agrega los repos
    run("helm repo add prometheus-community https://prometheus-community.github.io/helm-charts")
    run("helm repo add grafana https://grafana.github.io/helm-charts")
    run("helm repo update")

    # 2. Deploy de Prometheus
    run(f"helm upgrade --install prometheus prometheus-community/prometheus -n {NAMESPACE} --create-namespace -f values-custom.yaml")
    # 3. Deploy de Grafana
    run(f"helm upgrade --install grafana grafana/grafana -n {NAMESPACE} --set adminPassword={GRAFANA_ADMIN_PASSWORD} --set service.type=ClusterIP")

    # 4. Deploy kube-state-metrics
    run(f"helm upgrade --install kube-state-metrics prometheus-community/kube-state-metrics -n {NAMESPACE} --set serviceMonitor.enabled=false")

    # 5. Deploy de Ingress para Grafana (el manifiesto debe estar en monitor-ingress.yaml)
    run(f"kubectl apply -f monitor-ingress.yaml")
    
    # 6. Espera que Grafana levante
    wait_for_grafana()

    # 7. Crea el datasource de Prometheus
    create_grafana_datasource()

    # 8. Instala el dashboard (ejemplo: k8s-dashboard.json)
    if os.path.exists("k8s-dashboard.json"):
        import_grafana_dashboard("k8s-dashboard.json")
    else:
        print("No se encontró el archivo k8s-dashboard.json, omitiendo importación de dashboard.")

    print("\nListo! Accede a Grafana en http://grafana.local (user: admin, pass: admin)")

if __name__ == "__main__":
    main()
