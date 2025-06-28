# Simple App en kubernetes

---

## Menu
- [1. Challenge: Contexto y Objetivos](#1-challenge-contexto-y-objetivos)
  - [1.1 Objetivo](#11-objetivo)
  - [1.2 Enunciado](#12-enunciado)
  - [1.3 Bonus](#13-bonus)
- [2. Overlay Script Setup](#overlay-script-setup)
  - [2.1 Requisitos previos](#21-requisitos-previos)
  - [2.2 Instalación y Primeros Pasos](#22-instalación-y-primeros-pasos)
  - [2.3 Uso interactivo del script](#23-uso-interactivo-del-script)
  - [2.5 Overlay Manual Setup (sin script)](#25-overlay-manual-setup-sin-script)
  - [2.6 Detalles de las variables y templates](#26-detalles-de-las-variables-y-templates)
  - [2.7 Parámetros soportados por el script](#27-parámetros-soportados-por-el-script)
- [3. CI/CD Pipeline](#3-cicd-pipeline)
  - [3.1 Configuración](#31-configuración)
  - [3.2 Uso](#32-uso)
  - [3.3 Flujo del pipeline](#33-flujo-del-pipeline)
- [4. Kubernetes Monitoring Stack - Helm](#4-kubernetes-monitoring-stack---helm)
  - [4.1 Requisitos](#41-requisitos)
  - [4.2 Archivos necesarios](#42-archivos-necesarios)
  - [4.3 Instalación de dependencias Python](#43-instalación-de-dependencias-python)
  - [4.4 Ejecución](#44-ejecución)
  - [4.5 Eliminación](#45-eliminación)
- [5. Buenas prácticas y tips](#5-buenas-prácticas-y-tips)
- [6. Ejemplo de estructura final del repositorio](#6-ejemplo-de-estructura-final-del-repositorio)
- [7. Ejemplo de template `kustomization.yaml`](#7-ejemplo-de-template-kustomizationyaml)
- [8. Notas finales](#8-notas-finales)

# 1. Challenge Contexto y Objetivos

## 1.1 Objetivo 

Configurar una aplicación simple (por ejemplo, una API o una app web de ejemplo) usando manifiestos de Kubernetes organizados con Kustomize, de forma que permita su despliegue en diferentes entornos (dev, staging y prod) con variaciones mínimas entre ellos. 

[Volver](#menu)

## 1.2 Enunciado
Se te entrega una aplicación sencilla (puede ser una imagen de nginx) y se te pide:

* Una estructura de directorios donde residan las diferentes definiciones de artefactos (deployment, service, ingress, config-map) estructurados para ser utilizados en tres entornos (dev, staging y prod) utilizando kustomize en su despliegue

* Los diferentes entornos sólo difieren en:
  * Una variable de entorno APP_ENV que contendrá un valor diferenciando cada entorno ("dev", "staging", "pro")
  * El número de réplicas del pod 1, 2 y 3 respectivamente
  * Los recursos requeridos y límite del pod

* Se entregará:
  * La estrucutra de ficheros yaml en el repositorio.
  * Un readme explicando la ejecución de kustomize para el despliegue de cada entorno.
  * Todo añadido que se quiera incluir en el repositorio, debidamente documentado

[Volver](#menu)

## 1.3 Bonus

En esta sección se proponen desafíos adicionales para quienes deseen profundizar en la automatización y buenas prácticas en Kubernetes. Los bonus no son obligatorios, pero permiten demostrar conocimientos avanzados en integración continua, despliegue automatizado, escalado dinámico y uso de herramientas complementarias. Cada punto está pensado para ampliar el alcance del reto principal y enriquecer la solución final.

* CI: Crear un github action para construir la imágen docker que incluya un html "Hola Mundo" en el nginx. 

* CD: Explicar en un readme cómo se implementaría el despliegue en kubernetes utilizando un enfoque "gitops".

* Autoscaler: Añadir un manifiesto para un HorizontalPodAutoscaler para el entorno de prod.

* Uso de Kro: Añadir una rama para realizar el mismo despliegue utilizando [KRO](https://github.com/kro-run/kro)

* Otros: Cualquier añadido adicional en el que mostrar capacidad técnica: scripts de arranque de cluster local para probar, despliegue y uso de sistemas de monitorización para y captura de logs, infraestructura como código para la creación del cluster, etc.

[Volver](#menu)


## 2. Overlay Script Setup

**Overlay Setup** es un script interactivo en Python para facilitar la generación, mantenimiento y eliminación de overlays de Kustomize en proyectos Kubernetes. Automatiza la creación de archivos `kustomization.yaml`, patches, HPA e Ingress, tomando todos los parámetros desde preguntas interactivas y/o archivos `.env.<environment>`. También permite borrar overlays completos, limpiar recursos en el clúster y mantener tu repo limpio.

---

## 2.1 Requisitos previos

- Python 3 (recomendado 3.7+)
- Acceso a terminal/shell
- Tener instalado `kubectl` y acceso al clúster (opcional para aplicar/eliminar recursos)
- Carpeta de trabajo típica de K8s:
  ```
  k8s/
    base/
    overlays/
    templates/
      kustomization.yaml
      hpa.yaml
      patch-deployment.yaml
      patch-ingress.yaml
    overlay-setup.py
  ```

[Volver](#menu)

---

## 2.2 Instalación y Primeros Pasos

1. **Ubicá el script** dentro de tu carpeta `k8s/`.

2. **Asegurate de tener la carpeta template** y dentro, los archivos base:

   - `env.template`
   - `kustomization.yaml` (con variables `${VARIABLE}`)
   - `hpa.yaml`
   - `patch-deployment.yaml`
   - `patch-ingress.yaml`

3. Dale permisos de ejecución al script (opcional en Linux/Mac):

   ```sh
   chmod +x overlay-setup.py
   ```

4. Instalá dependencias si tu Python lo requiere (el script solo usa librerías estándar).

[Volver](#menu)

---

## 2.3 Uso interactivo del script

### Crear un nuevo overlay

```sh
python3 overlay-setup.py
# o 
python overlay-setup.py

```

El script te va a guiar paso a paso con preguntas:

- ¿Qué environment es? (`dev`, `prod`, etc.)
- ¿El nombre del environment se usa como namespace?
- Si usás ingress: clase, host y path
- Si usás HPA: min/max réplicas y CPU averageUtilization
- Mensaje Personalizado, solo para test al abrir la aplicacion.

Cuando termina:

- Crea el archivo `.env.<environment>` con todos los parámetros.
- Genera la carpeta del overlay y todos los archivos (kustomization.yaml, hpa.yaml, patch-deployment.yaml, patch-ingress.yaml) ya parametrizados.
- Te pregunta si querés aplicar el overlay directamente con `kubectl apply -k overlays/<environment>`

### Eliminar un overlay y sus recursos

```sh
python3 overlay-setup.py --delete <env>
# o
python3 overlay-setup.py -d <env>
```
> [!tip] La ejecucion del script con python3 es de uso ilustrativo. Utilizar python3 o python segun lo configurado en el entorno que se va a utilizar el script.

- Borra la carpeta del overlay, el archivo `.env.<env>`, y si querés, elimina también los recursos en el clúster (`kubectl delete -k overlays/<env>`)
- Si la carpeta `overlays/` queda vacía, la borra automáticamente.

### Listar overlays existentes

```sh
python3 overlay-setup.py --list
# o
python3 overlay-setup.py -l
```

> [!tip] La ejecucion del script con python3 es de uso ilustrativo. Utilizar python3 o python segun lo configurado en el entorno que se va a utilizar el script.

[Volver](#menu)


## 2.4 Overlay Manual Setup (sin script)

### Copiar y modificar archivos desde

1. Elegí un environment, por ejemplo `dev`.
2. Copiá la carpeta `templates/` completa dentro de `overlays/dev/` (o solo los archivos necesarios).
3. Renombrá y editá los archivos para tu caso:
   - `kustomization.yaml` → reemplazá a mano los `${VARIABLE}` por los valores deseados
   - `hpa.yaml`, `patch-deployment.yaml`, `patch-ingress.yaml` igual
4. Si querés podés crear un archivo `.env.dev` solo para tu referencia (el script lo usa, pero manualmente no es obligatorio).
5. Modificá el `kustomization.yaml` para incluir/excluir recursos y patches según necesites (por ejemplo, incluir `hpa.yaml` solo si usás HPA).
6. Aplicá el overlay manualmente con:
   ```sh
   kubectl apply -k overlays/dev
   ```

[Volver](#menu)

## 2.5 Detalles de las variables y templates

- **No variabilices nunca** el nombre del ConfigMap, Deployment, Service, etc. si usás `behavior: replace` o patch. Siempre deben coincidir con el base.
- Sí podés variabilizar:
  - Namespace, imagen, tag, réplicas, literales, valores de entorno.
- Si usás `.env.<environment>` para generación automática, el script toma todos los valores desde ahí.

[Volver](#menu)

## 2.6 Parámetros soportados por el script

- `--help` o `-h`: muestra la ayuda
- `--list` o `-l`: lista overlays creados
- `--delete <env>` o `-d <env>`: borra el overlay y archivo `.env` correspondiente (opcionalmente también los recursos del cluster)

[Volver](#menu)

---
## 3. CI/CD Pipeline

- Construye la imagen Docker automáticamente al hacer push a las ramas `dev` o `prod`.
- Genera un tag semántico para cada versión de la imagen (por ejemplo: `1.2.3-dev1` para desarrollo, `1.2.3` para producción).
- Subida automática de la imagen a Docker Hub con el tag generado.
- Si es un push a `prod`, crea un release en GitHub con el changelog del build.

## 3.1 Configuración

#### Variables de entorno / Secrets

Debes configurar los siguientes **Secrets** en tu repositorio de GitHub:

| Variable              | Descripción                              |
|-----------------------|------------------------------------------|
| `DOCKERHUB_USERNAME`  | Tu usuario de Docker Hub                 |
| `DOCKERHUB_TOKEN`     | Token de acceso (no tu password normal)  |

[Volver](#menu)

## 3.2 Uso

### **Push a `dev`**

- Cada push a la rama `dev` construirá una imagen Docker y la subirá a Docker Hub con un tag del tipo:  
  ```
  <DOCKERHUB_USERNAME>/nginx-custom-html:1.2.3-dev1
  ```

### **Push a `prod`**

- Cada push a la rama `prod` construirá una imagen Docker y la subirá con un tag tipo:  
  ```
  <DOCKERHUB_USERNAME>/nginx-custom-html:1.2.3
  ```
- Además, se creará un **Release** en GitHub con el changelog de cambios detectados.

[Volver](#menu)

## 3.3 Flujo del pipeline

1. **Set Environment**  
   Detecta si el push es a `dev` o `prod` y configura las variables.
2. **Versionado Semántico**  
   Calcula la nueva versión usando los commits y la estrategia definida.
3. **Tag y Release (sólo prod)**  
   Publica un nuevo tag en el repo y, en prod, genera un Release en GitHub.
4. **Docker Build & Push**  
   Construye la imagen Docker y la sube a Docker Hub usando el tag generado.

[Volver](#menu)

---

## 4. Kubernetes Monitoring Stack - Helm

Automatiza el despliegue de Prometheus, Grafana y dashboards personalizados en tu cluster Kubernetes usando Helm y Python.

## 4.1 Requisitos

- Cluster Kubernetes (Docker Desktop, Minikube, etc.) con `kubectl` configurado
- `helm` instalado y accesible en PATH
- Python 3.7+ y `pip` instalados

[Volver](#menu)

## 4.2 Archivos necesarios

- `setup_monitoring.py` (script principal)
- `values-custom.yaml` (configuración Prometheus extra scrape)
- `grafana-ingress.yaml` (manifiesto Ingress para Grafana)
- `k8s-dashboard.json` (JSON del dashboard que desees importar)
- `requirements.txt` (dependencias Python)

[Volver](#menu)

## 4.3 Instalación de dependencias Python

```bash
pip install -r requirements.txt
```
[Volver](#menu)

## 4.4 Ejecución

```bash
python3 setup_monitoring.py
```
> [!tip] La ejecucion del script con python3 es de uso ilustrativo. Utilizar python3 o python segun lo configurado en el entorno que se va a utilizar el script.


El script:
- Agrega los repos Helm y deploya Prometheus, Grafana y kube-state-metrics
- Aplica el manifiesto de Ingress para Grafana
- Espera que Grafana esté disponible vía ingress
- Configura el datasource de Prometheus en Grafana
- Importa el dashboard de Kubernetes

[Volver](#menu)

## 4.5 Eliminación

Para la eliminación de prometheus y grafana:

```bash
python3 setup_monitoring.py -d
```
> [!tip] La ejecucion del script con python3 es de uso ilustrativo. Utilizar python3 o python segun lo configurado en el entorno que se va a utilizar el script.

Esto elimina:
- Las releases de Helm de Prometheus, Grafana y kube-state-metrics en el namespace que se haya indicado
- Los ingress de Grafana y Prometheus por nombre (no depende del archivo)

```bash
helm uninstall prometheus -n monitoring
helm uninstall grafana -n monitoring
helm uninstall kube-state-metrics -n monitoring
kubectl delete -f grafana-ingress.yaml -n monitoring
```
[Volver](#menu)

## 5. Buenas prácticas y tips

- Utilizar un enfoque GitOps para manejar los despliegues en Kubernetes, versionando todos los manifiestos en los repositorios y automatizando los despliegues con herramientas como ArgoCD. Esto permite mantener el estado del clúster sincronizado con lo que está en Git y facilita los rollbacks.
- Utilizar la misma estructura de carpetas para todos los entornos.
- Hacer commits del directorio `templates/` para que todo el equipo tenga el mismo punto de partida.
- No borrar overlays si aún están aplicados en el clúster, a menos que primero se limpien los recursos.
- Si se crean o borran overlays manualmente, asegurarse de mantener actualizado el repositorio (y los archivos `.env` de referencia).
- En ambientes reales, asegurarse de que los secrets **no sean expuestos** ni en los archivos YAML ni en documentación pública.

[Volver](#menu)

---

## 6. Ejemplo de estructura final del repositorio

```
.github/
  workflows/
    build.yml
k8s/
  base/
  overlays/
    dev/
      kustomization.yaml
      hpa.yaml
      patch-deployment.yaml
      patch-ingress.yaml
    prod/
      ...
  templates/
    kustomization.yaml
    hpa.yaml
    patch-deployment.yaml
    patch-ingress.yaml
  .env.dev
  .env.prod
  overlay-setup.py
src/
  html/
    index.php
Dockerfile
README.MD
```
[Volver](#menu)

---

## 7. Ejemplo de template `kustomization.yaml`

```yaml
namespace: ${NAMESPACE}

resources:
  - ../../base
${HPA_RESOURCES}

configMapGenerator:
  - name: nginx-app-config  # ¡No cambiar el nombre!
    behavior: replace
    literals:
      - APP_ENV=${APP_ENV}
      - CUSTOM_MESSAGE=${CUSTOM_MESSAGE}

${PATCHES}
```
[Volver](#menu)

---

## 8. Notas finales

- El script está pensado para facilitar equipos que repiten overlays y no quieren copiar/pegar ni olvidarse parámetros clave.
- Toda modificación manual es posible, pero asegurate de no romper la relación entre base y overlays (especialmente los nombres de recursos).
- Si usás otros tipos de patches, sumá tus templates a la carpeta y ajustá el script o el flujo manual según tu caso.

[Volver](#menu)

