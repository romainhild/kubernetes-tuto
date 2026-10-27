# Étape 3 — Le Deployment

Un **Deployment** ne gère pas directement des Pods : il gère des
**ReplicaSets**, et sait faire la transition entre deux versions d'un
ReplicaSet sans coupure de service. C'est la ressource que tu utiliseras
le plus souvent au quotidien pour des applications sans état (stateless).

## Nouveau fichier

- `k8s/deployment.yaml` — remplace `k8s/replicaset.yaml`. Même template
  de Pod, mais avec une stratégie de mise à jour explicite, plus deux
  "probes" (voir plus bas).

## Essayer

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get deployments,replicasets,pods
```

Remarque : le Deployment a créé un ReplicaSet (nommé `web-<hash>`) qui a
lui-même créé les 3 Pods. Trois niveaux : Deployment → ReplicaSet → Pod.

## Démonstration : une mise à jour sans coupure

Modifie `app/index.html` (par exemple change le texte), reconstruis
l'image avec un **nouveau tag** :

```bash
minikube image build -t local/k8s-tutorial-web:v2 app/
```

Édite `k8s/deployment.yaml` pour utiliser `local/k8s-tutorial-web:v2`,
puis :

```bash
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/web
kubectl get replicasets
```

Tu vas voir un **nouveau** ReplicaSet monter en puissance pendant que
l'ancien redescend — jamais plus de `replicas + maxSurge` Pods au total,
jamais moins de `replicas - maxUnavailable` Pods disponibles. C'est
réglé ici en `maxSurge: 1` / `maxUnavailable: 0` : zéro interruption,
au prix d'un Pod temporairement en plus.

## Les stratégies de mise à jour

- **`RollingUpdate`** (par défaut) : remplace les Pods progressivement.
  - `maxSurge` : combien de Pods en plus du compte demandé peuvent
    exister pendant la transition (en nombre ou en %).
  - `maxUnavailable` : combien de Pods peuvent être indisponibles pendant
    la transition.
- **`Recreate`** : détruit tous les anciens Pods avant de créer les
  nouveaux. Coupure de service garantie, mais utile quand deux versions
  ne peuvent pas cohabiter (ex: migration de schéma de base incompatible).

## Revenir en arrière

```bash
kubectl rollout history deployment/web
kubectl rollout undo deployment/web
```

## Les probes (pourquoi elles comptent ici)

- **`readinessProbe`** : tant qu'elle échoue, le Pod n'est pas considéré
  "prêt" — il ne reçoit pas de trafic (via un Service, étape suivante) et
  n'est pas compté dans le calcul du rolling update. C'est ce qui permet
  au Deployment de savoir qu'un nouveau Pod est vraiment prêt avant de
  couper l'ancien.
- **`livenessProbe`** : si elle échoue de façon répétée, Kubernetes tue
  et redémarre le conteneur. Utile si l'appli peut se retrouver "bloquée"
  sans crasher.

## Étape suivante

```bash
git checkout step-4-service
cat STEP.md
```

Pour l'instant on accède toujours à l'appli via `kubectl port-forward`.
On va enfin exposer ça proprement avec un **Service**.
