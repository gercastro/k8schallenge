# kubernetes

## Objetivo
Configurar una aplicación simple (por ejemplo, una API o una app web de ejemplo) usando manifiestos de Kubernetes organizados con Kustomize, de forma que permita su despliegue en diferentes entornos (dev, staging y prod) con variaciones mínimas entre ellos.

## Enunciado
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

## Bonus (no es imprescindible)
### CI
* Crear un github action para construir la imágen docker que incluya un html "Hola Mundo" en el nginx
### CD
* Explicar en un readme cómo se implementaría el despliegue en kubernetes utilizando un enfoque "gitops" 
### Autoscaler
* Añadir un manifiesto para un HorizontalPodAutoscaler para el entorno de prod.
### Uso de Kro
* Añadir una rama para realizar el mismo despliegue utilizando [KRO](https://github.com/kro-run/kro)
### Otros
* Cualquier añadido adicional en el que mostrar capacidad técnica: scripts de arranque de cluster local para probar, despliegue y uso de sistemas de monitorización para y captura de logs, infraestructura como código para la creación del cluster, etc.
