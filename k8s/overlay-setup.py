#!/usr/bin/env python3
import os
import sys
import shutil

def preguntar_sobrescribir(objeto, path):
    resp = input(f"Ya existe {objeto}: '{path}'. ¿Querés sobrescribirlo? (s/n): ").strip().lower()
    return resp in ["s", "y"]

def pregunta_numero(mensaje, valor_default):
    val = input(f"{mensaje} (default: {valor_default}): ").strip()
    return val if val.isdigit() and int(val) > 0 else str(valor_default)

def print_help():
    print("""
Uso:
  python3 overlay-setup.py                            # Ejecuta el modo interactivo para crear overlays y .env
  python3 overlay-setup.py --delete <env> | -d <env>  # Elimina el overlay <env>
  python3 overlay-setup.py --list | -l                # Lista todos los overlays existentes
  python3 overlay-setup.py --help | -h                # Muestra esta ayuda
""")

# Permitir flags: --delete/-d, --list/-l, --help/-h
if len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h"):
    print_help()
    sys.exit(0)

if len(sys.argv) == 3 and sys.argv[1] in ("--delete", "-d"):
    env = sys.argv[2]
    overlay_path = os.path.join("overlays", env)
    if os.path.isdir(overlay_path):
        # Preguntar si también quiere eliminar los recursos del cluster
        borrar_k8s = input(f"¿Querés eliminar TAMBIÉN los recursos desplegados en el cluster Kubernetes para este overlay? (kubectl delete -k {overlay_path}) (s/n): ").strip().lower()
        if borrar_k8s in ["s", "y"]:
            exit_code = os.system(f"kubectl delete -k {overlay_path}")
            if exit_code == 0:
                print("Recursos de Kubernetes eliminados.")
            else:
                print("Hubo un error eliminando los recursos de Kubernetes.")

        confirm = input(f"¿Seguro que querés eliminar la carpeta '{overlay_path}' y todo su contenido? (s/n): ").strip().lower()
        if confirm in ["s", "y"]:
            shutil.rmtree(overlay_path)
            print(f"Carpeta '{overlay_path}' eliminada.")
            env_file = f".env.{env}"
            if os.path.isfile(env_file):
                try:
                    os.remove(env_file)
                    print(f"Archivo '{env_file}' eliminado.")
                except Exception as e:
                    print(f"No se pudo eliminar '{env_file}': {e}")
            else:
                print(f"No existe el archivo '{env_file}'.")
            overlays_dir = "overlays"
            if os.path.isdir(overlays_dir) and not os.listdir(overlays_dir):
                try:
                    os.rmdir(overlays_dir)
                    print(f"Carpeta '{overlays_dir}' eliminada (ya no quedaban overlays).")
                except Exception as e:
                    print(f"No se pudo eliminar '{overlays_dir}': {e}")
        else:
            print("Eliminación cancelada.")
    else:
        print(f"No existe la carpeta '{overlay_path}'.")
    sys.exit(0)

if len(sys.argv) == 2 and sys.argv[1] in ("--list", "-l"):
    overlays_dir = "overlays"
    if not os.path.isdir(overlays_dir):
        print("No existe la carpeta 'overlays'.")
    else:
        overlays = [d for d in os.listdir(overlays_dir) if os.path.isdir(os.path.join(overlays_dir, d))]
        if overlays:
            print("Overlays existentes:")
            for overlay in overlays:
                print(f"  - {overlay}")
        else:
            print("No hay overlays creados.")
    sys.exit(0)

if len(sys.argv) > 1:
    print("Parámetro/s incorrectos.")
    print_help()
    sys.exit(1)

print("==== Kustom Overlay Setup: Generador de archivos .env interactivo ====\n")

environment = input("¿Qué environment es? (por ejemplo: dev, prod): ").strip()

use_env_as_namespace = input(f"¿El nombre del environment ('{environment}') se va a usar para el namespace? (s/n): ").strip().lower()
if use_env_as_namespace in ["s", "y"]:
    namespace = environment
else:
    namespace = input("¿Cuál es el namespace?: ").strip()

app_env = environment

env_file = f".env.{environment}"

use_ingress_patch = input("¿Va a usar Ingress? (s/n): ").strip().lower() in ["s", "y"]
use_hpa = input("¿Va a usar Autoscaler (HPA)? (s/n): ").strip().lower() in ["s", "y"]
custom_message = input("Mensaje personalizado (CUSTOM_MESSAGE): ").strip()

if not use_hpa:
    while True:
        replicas = input("¿Cuántas réplicas para el Deployment? (número entero): ").strip()
        if replicas.isdigit() and int(replicas) > 0:
            break
        print("Por favor, ingresá un número entero positivo.")
else:
    replicas = "1"
    min_replicas = pregunta_numero("MinReplicas (para Autoscaler (HPA))", 3)
    max_replicas = pregunta_numero("MaxReplicas (para Autoscaler (HPA))", 7)
    cpu_average_utilization = pregunta_numero("CPU averageUtilization (%) (para Autoscaler (HPA))", 50)

if use_ingress_patch:
    print(f"\n--- Configuración de Ingress---")
    ingress_class_name = input("ingressClass (default: nginx): ").strip() or "nginx"
    host = input("FQDN (default: example.local): ").strip() or "example.local"
    path = input("Path (default: /): ").strip() or "/"

docker_image_tag = input("Docker image tag (default: latest): ").strip() or "latest"

if custom_message.startswith('"') and custom_message.endswith('"'):
    custom_message = custom_message[1:-1]
elif custom_message.startswith("'") and custom_message.endswith("'"):
    custom_message = custom_message[1:-1]

with open(env_file, "w") as f:
    f.write(f"NAMESPACE={namespace}\n")
    f.write(f"APP_ENV={app_env}\n")
    f.write(f'CUSTOM_MESSAGE="{custom_message}"\n')
    f.write(f"USE_HPA={'true' if use_hpa else 'false'}\n")
    f.write(f"USE_INGRESS_PATCH={'true' if use_ingress_patch else 'false'}\n")
    if not use_hpa:
        f.write(f"REPLICAS={replicas}\n")
    else:
        f.write(f"MIN_REPLICAS={min_replicas}\n")
        f.write(f"MAX_REPLICAS={max_replicas}\n")
        f.write(f"CPU_AVERAGE_UTILIZATION={cpu_average_utilization}\n")
    if use_ingress_patch:
        f.write(f"INGRESS_CLASS_NAME={ingress_class_name}\n")
        f.write(f"HOST={host}\n")
        f.write(f"PATH={path}\n")
    f.write(f"DOCKER_IMAGE_TAG={docker_image_tag}\n")

print(f"\nArchivo {env_file} generado con éxito:")
with open(env_file) as f:
    print("\n---")
    print(f.read())
    print("---\n")

# --- FLUJO DE CREACIÓN DEL OVERLAY ---
run_overlay = input("¿Querés generar el overlay ahora? (s/n): ").strip().lower()
if run_overlay in ["s", "y"]:
    overlays_dir = "overlays"
    env_dir = os.path.join(overlays_dir, environment)
    kustom_file = os.path.join(env_dir, "kustomization.yaml")

    # 1. Chequear si existe la carpeta overlays/
    if os.path.isdir(overlays_dir):
        print(f"Carpeta de overlays EXISTE: '{overlays_dir}'")
    else:
        print(f"Carpeta de overlays NO existe: '{overlays_dir}'")
        os.makedirs(overlays_dir)
        print(f"Se creó la carpeta: '{overlays_dir}'")

    # 2. Chequear si existe la carpeta del env
    if os.path.isdir(env_dir):
        print(f"Carpeta del environment EXISTE: '{env_dir}'")
        if not preguntar_sobrescribir("la carpeta del environment", env_dir):
            print("Se cancela la generación del overlay.")
            exit(0)
        # Si va a sobrescribir, podría limpiar archivos viejos si querés
    else:
        print(f"Carpeta del environment NO existe: '{env_dir}'")
        os.makedirs(env_dir)
        print(f"Se creó la carpeta: '{env_dir}'")

    # 3. Chequear si existe kustomization.yaml
    if os.path.isfile(kustom_file):
        print(f"El archivo 'kustomization.yaml' EXISTE en '{env_dir}'")
        if not preguntar_sobrescribir("el archivo kustomization.yaml", kustom_file):
            print("Se cancela la generación del overlay.")
            exit(0)

    # 4. Crear kustomization.yaml (con variables)
    # Usa un template, o podés hardcodear el contenido acá para demo
    template_path = os.path.join("templates", "kustomization.yaml")
    if os.path.isfile(template_path):
        # Leer template y reemplazar variables
        with open(template_path) as f:
            content = f.read()
        content = content.replace("${NAMESPACE}", namespace)
        content = content.replace("${APP_ENV}", app_env)
        content = content.replace("${CUSTOM_MESSAGE}", custom_message)
        content = content.replace("${HP_RESOURCES}", "  - hpa.yaml" if use_hpa else "")
        content = content.replace("${INGRES_PATCH}", "  - path: patch-ingress.yaml" if use_ingress_patch else "")

        with open(kustom_file, "w") as f:
            f.write(content)
        print(f"\nArchivo '{kustom_file}' generado con éxito.\n")
    else:
        print(f"Template kustomization.yaml NO encontrado en {template_path}")
        exit(1)

    # Path al template
    patch_deployment_template = os.path.join("templates", "patch-deployment.yaml")
    patch_deployment_dest = os.path.join(env_dir, "patch-deployment.yaml")

    if os.path.isfile(patch_deployment_template):
        with open(patch_deployment_template) as f:
            patch_content = f.read()
        patch_content = patch_content.replace("${REPLICAS}", replicas)
        patch_content = patch_content.replace("${DOCKER_IMAGE_TAG}", docker_image_tag)
        # Si parametrizás más cosas, reemplazá también esas variables acá
        with open(patch_deployment_dest, "w") as f:
            f.write(patch_content)
        print(f"Archivo '{patch_deployment_dest}' generado con éxito.\n")
    else:
        print(f"Template patch-deployment.yaml NO encontrado en {patch_deployment_template}")
        exit(1)


    if use_hpa:
        hpa_template = os.path.join("templates", "hpa.yaml")
        hpa_dest = os.path.join(env_dir, "hpa.yaml")

        if os.path.isfile(hpa_template):
            with open(hpa_template) as f:
                hpa_content = f.read()
            hpa_content = hpa_content.replace("${MIN_REPLICAS}", min_replicas)
            hpa_content = hpa_content.replace("${MAX_REPLICAS}", max_replicas)
            hpa_content = hpa_content.replace("${CPU_AVERAGE_UTILIZATION}", cpu_average_utilization)
            # Otros replaces si hay más variables
            with open(hpa_dest, "w") as f:
                f.write(hpa_content)
            print(f"Archivo '{hpa_dest}' generado con éxito.\n")
        else:
            print(f"Template hpa.yaml NO encontrado en {hpa_template}")
            exit(1)

    if use_ingress_patch:
        patch_ingress_template = os.path.join("templates", "patch-ingress.yaml")
        patch_ingress_dest = os.path.join(env_dir, "patch-ingress.yaml")

        if os.path.isfile(patch_ingress_template):
            with open(patch_ingress_template) as f:
                patch_ingress_content = f.read()
            patch_ingress_content = patch_ingress_content.replace("${INGRESS_CLASS_NAME}", ingress_class_name)
            patch_ingress_content = patch_ingress_content.replace("${HOST}", host)
            patch_ingress_content = patch_ingress_content.replace("${PATH}", path)  
            with open(patch_ingress_dest, "w") as f:
                f.write(patch_ingress_content)
            print(f"Archivo '{patch_ingress_dest}' generado con éxito.\n")
        else:
            print(f"Template patch-ingress.yaml NO encontrado en {patch_ingress_template}")
            exit(1)

run_kubectl = input(f"\n¿Querés ejecutar 'kubectl apply -k overlays/{environment}' ahora? (s/n): ").strip().lower()
if run_kubectl in ["s", "y"]:
    exit_code = os.system(f"kubectl apply -k overlays/{environment}")
    if exit_code == 0:
        print("¡Overlay aplicado exitosamente!")
    else:
        print("Hubo un error aplicando el overlay.")
else:
    print("\n¡Listo! Si necesitás otro environment, ejecutá de nuevo este script.\n")
    print("Podés aplicar el overlay más tarde con:")
    print(f"kubectl apply -k overlays/{environment}")


