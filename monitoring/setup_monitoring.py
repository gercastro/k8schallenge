import subprocess
import time
import sys
import requests
import json
import os

NAMESPACE = "monitoring"
GRAFANA_INGRESS_HOST = "grafana.local"
GRAFANA_ADMIN_USER = "admin"
GRAFANA_ADMIN_PASSWORD = "admin"

def run(cmd):
    print(f"-> Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(result.returncode)
    return result.stdout

def delete_everything(namespace):
    print("Eliminando todo lo instalado con Helm y kubectl...")
    run(f"helm uninstall prometheus -n {namespace}")
    run(f"helm uninstall grafana -n {namespace}")
    run(f"helm uninstall kube-state-metrics -n {namespace}")
    run(f"kubectl delete -f monitor-ingress.yaml -n {namespace}")
    print("Todo eliminado. Revisá el namespace si querés borrar recursos huérfanos.")

def wait_for_grafana(grafana_ingress_fqdn):
    print("Esperando que Grafana esté lista en el cluster...")
    for _ in range(30):
        try:
            r = requests.get(f"http://{grafana_ingress_fqdn}/login", timeout=2)
            if r.status_code == 200:
                print("Grafana responde!")
                return
        except Exception:
            pass
        time.sleep(5)
    print("No se pudo acceder a Grafana en el Ingress. Revisá el despliegue.")
    sys.exit(1)

def create_grafana_datasource(grafana_ingress_fqdn, prometheus_svc_dns):
    print("Esperando que Grafana esté lista...")
    wait_for_grafana(grafana_ingress_fqdn)
    print("Configurando DataSource de Prometheus en Grafana...")
    url = f"http://{grafana_ingress_fqdn}/api/datasources"
    headers = {"Content-Type": "application/json"}
    auth = (GRAFANA_ADMIN_USER, GRAFANA_ADMIN_PASSWORD)
    payload = {
        "name": "Prometheus",
        "type": "prometheus",
        "access": "proxy",
        "url": prometheus_svc_dns,
        "basicAuth": False,
        "isDefault": True,
    }
    r = requests.post(url, headers=headers, auth=auth, json=payload)
    if r.status_code in (200, 409):  # 409 = ya existe
        print("Datasource configurado.")
    else:
        print("Error al configurar el datasource:", r.text)
        sys.exit(1)

def import_grafana_dashboard(json_file, grafana_ingress_fqdn):
    print(f"Importando dashboard {json_file} en Grafana...")
    url = f"http://{grafana_ingress_fqdn}/api/dashboards/import"
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

def render_values_yaml(namespace):
    # Lee el template y reemplaza el namespace
    with open("values-custom.template.yaml", "r") as f:
        content = f.read()
    content = content.replace("{{NAMESPACE}}", namespace)
    with open("values-custom.yaml", "w") as f:
        f.write(content)

def main():

    is_delete = '-d' in sys.argv or '--delete' in sys.argv
    
    namespace = input(f"Namespace para el monitoreo (default: {NAMESPACE}): ").strip() or NAMESPACE
    
    if is_delete:
        delete_everything(namespace)
        sys.exit(0)

    usa_kube_state_metrics = input("¿Usar kube-state-metrics? (s/n): ").strip().lower() in ["s", "y"]
    grafana_ingress_fqdn = input(f"FQDN para Grafana (default: {GRAFANA_INGRESS_HOST}): ").strip() or GRAFANA_INGRESS_HOST
    prometheus_svc_dns = f"http://prometheus-server.{namespace}.svc.cluster.local"


    # 1. Agrega los repos
    run("helm repo add prometheus-community https://prometheus-community.github.io/helm-charts")
    run("helm repo add grafana https://grafana.github.io/helm-charts")
    run("helm repo update")

    # 2. Deploy de Prometheus
    run(f"helm upgrade --install prometheus prometheus-community/prometheus -n {namespace} --create-namespace -f values-custom.yaml")
    # 3. Deploy de Grafana
    run(f"helm upgrade --install grafana grafana/grafana -n {namespace} --set adminPassword={GRAFANA_ADMIN_PASSWORD} --set service.type=ClusterIP")

    # 4. Deploy kube-state-metrics
    run(f"helm upgrade --install kube-state-metrics prometheus-community/kube-state-metrics -n {namespace} --set serviceMonitor.enabled=false") if usa_kube_state_metrics else print("kube-state-metrics no se instalará porque la opción fue deshabilitada.")

    # 5. Deploy de Ingress para Grafana (el manifiesto debe estar en monitor-ingress.yaml)
    run(f"kubectl apply -f monitor-ingress.yaml -n {namespace}")
    
    # 6. Espera que Grafana levante
    wait_for_grafana(grafana_ingress_fqdn)

    # 7. Crea el datasource de Prometheus
    create_grafana_datasource(grafana_ingress_fqdn, prometheus_svc_dns)

    # 8. Instala el dashboard (ejemplo: k8s-dashboard.json)
    if os.path.exists("k8s-dashboard.json"):
        import_grafana_dashboard("k8s-dashboard.json", grafana_ingress_fqdn)
    else:
        print("No se encontró el archivo k8s-dashboard.json, omitiendo importación de dashboard.")

    print(f"\nListo! Accede a Grafana en http://{grafana_ingress_fqdn} (user: admin, pass: admin)")

if __name__ == "__main__":
    main()
