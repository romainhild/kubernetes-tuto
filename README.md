# Tutoriel Kubernetes — d'une image Docker à une appli avec base de données

Ce repo est un tutoriel progressif pour apprendre Kubernetes. On part d'une
simple image Docker, et à chaque étape on ajoute **une** nouvelle couche
(un nouveau concept Kubernetes), jusqu'à obtenir une petite appli web
connectée à une base de données persistante.

Chaque étape est une **branche git**. Chaque branche part de la précédente :
elle contient donc tout ce qui a été introduit avant, plus la nouveauté du
jour. Tu peux à tout moment faire `git checkout <nom-de-branche>` pour
retrouver l'état exact d'une étape, sans avoir à rejouer les étapes
précédentes.

## Pré-requis

- [Docker](https://www.docker.com/) (pour construire les images)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
- [minikube](https://minikube.sigs.k8s.io/docs/start/) — `brew install minikube`

Démarrer le cluster local une fois pour toute la suite du tutoriel :

```bash
minikube start
kubectl get nodes
```

Pour tout nettoyer entre deux essais :

```bash
minikube delete
```

## Les étapes

| Branche | Concept introduit |
|---|---|
| [`step-0-docker`](../../tree/step-0-docker) | Une image Docker toute seule, sans Kubernetes |
| [`step-1-pod`](../../tree/step-1-pod) | Le Pod |
| [`step-2-replicaset`](../../tree/step-2-replicaset) | Le ReplicaSet |
| [`step-3-deployment`](../../tree/step-3-deployment) | Le Deployment (rolling update, rollback) |
| [`step-4-service`](../../tree/step-4-service) | Le Service (ClusterIP, NodePort, LoadBalancer...) |
| [`step-5-namespace`](../../tree/step-5-namespace) | Le Namespace |
| [`step-6-configmap`](../../tree/step-6-configmap) | Le ConfigMap |
| [`step-7-secret`](../../tree/step-7-secret) | Le Secret |
| [`step-8-database-pv`](../../tree/step-8-database-pv) | PersistentVolume / PersistentVolumeClaim + une vraie base de données |
| [`step-9-statefulset`](../../tree/step-9-statefulset) | Le StatefulSet |
| [`step-10-ingress`](../../tree/step-10-ingress) | L'Ingress |
| [`step-11-helm`](../../tree/step-11-helm) | Helm |

Chaque branche a, à sa racine, un fichier **`STEP.md`** qui explique :
- le concept introduit, pourquoi il existe et le problème qu'il résout,
- les différentes variantes/options du concept (ex: les types de Service),
- les commandes à exécuter pour l'essayer et observer le résultat,
- une ou deux manipulations pour "casser" des choses et comprendre le
  comportement (ex: supprimer un Pod géré par un ReplicaSet).

## Pour commencer

```bash
git checkout step-0-docker
cat STEP.md
```
