# Étape 13 — Le HorizontalPodAutoscaler

Jusqu'ici, le nombre de réplicas de `web` était une valeur fixe
(`web.replicaCount` dans `values.yaml`). Un **HorizontalPodAutoscaler**
(HPA) ajuste ce nombre automatiquement, à la hausse comme à la baisse,
en fonction d'une métrique observée — ici, l'utilisation CPU.

## Pré-requis : un fournisseur de métriques

Le HPA ne mesure rien lui-même : il lit l'API `metrics.k8s.io`, que
minikube n'active pas par défaut.

```bash
minikube addons enable metrics-server
kubectl top pods -n tutorial-app   # doit afficher du CPU/mémoire, pas une erreur
```

(`kubectl top` qui échoue est le symptôme numéro un d'un HPA qui reste
bloqué sur `<unknown>` — vois plus bas.)

## Ce qui change

- `chart/templates/hpa.yaml` (nouveau) : le HPA, togglable via
  `web.autoscaling.enabled`.
- `chart/templates/deployment.yaml` :
  - ajout de `resources.requests`/`limits` sur le conteneur — **obligatoire**
    pour le HPA : "80% d'utilisation CPU" ne veut rien dire sans un
    `request.cpu` de référence à partir duquel calculer ce pourcentage.
  - le champ `replicas:` devient conditionnel
    (`{{- if not .Values.web.autoscaling.enabled }}`) : si on le
    laissait toujours à `web.replicaCount`, chaque `helm upgrade`
    écraserait le nombre de Pods décidé par le HPA et repartirait de la
    valeur fixe — un conflit permanent entre Helm et l'autoscaler.

## Essayer

```bash
helm upgrade tuto chart/ --namespace tutorial-app
kubectl get hpa -n tutorial-app -w
```

Colonnes à surveiller : `TARGETS` (utilisation actuelle / cible, ex.
`3%/50%`) et `REPLICAS`. Si `TARGETS` reste bloqué sur `<unknown>/50%`
pendant plus d'une minute, c'est que `metrics-server` n'est pas prêt ou
pas activé — revérifie `kubectl top pods`.

## Générer de la charge pour voir le scale-up

```bash
kubectl create deployment load-generator -n tutorial-app \
  --image=busybox:1.36 --replicas=4 -- \
  /bin/sh -c "while true; do wget -q -O- http://web >/dev/null; done"

kubectl get hpa -n tutorial-app -w
```

Après quelques dizaines de secondes, `TARGETS` dépasse 50% et
`REPLICAS` grimpe au-delà de `minReplicas` (jusqu'à `maxReplicas=4` max
ici). Vérifie en parallèle :

```bash
kubectl get pods -n tutorial-app -l app=web
```

Arrête la charge :

```bash
kubectl delete deployment load-generator -n tutorial-app
```

`REPLICAS` redescend, mais **pas tout de suite** : par design, le
scale-down a un délai de stabilisation (5 minutes par défaut) pour
éviter du "flapping" (scale up/down en boucle sur un pic de charge
court). Réglable via `behavior.scaleDown.stabilizationWindowSeconds`
dans le spec du HPA — pas configuré ici pour rester simple, mais bon à
savoir.

## Comment le HPA décide

Toutes les ~15 secondes (le contrôleur n'est pas instantané), pour une
métrique de type `Resource` :

```
désiré = ceil(réplicas_actuels × (valeur_actuelle / valeur_cible))
```

Borné entre `minReplicas` et `maxReplicas`. C'est pour ça qu'on ne met
jamais `minReplicas: 0` avec ce genre de métrique : s'il y a 0 Pod, il
n'y a aucune métrique à mesurer pour décider de remonter.

## Les autres types de métriques (API `autoscaling/v2`)

- **`Resource`** (notre cas) : CPU ou mémoire, lu depuis `metrics-server`
  — pas besoin d'instrumenter l'appli.
- **`Pods`** : une métrique personnalisée, moyennée par Pod (ex: requêtes/seconde
  par Pod).
- **`Object`** : une métrique lue sur un *autre* objet Kubernetes (ex: la
  longueur d'une file portée par un Service).
- **`External`** : une métrique qui ne vient pas du cluster du tout (ex:
  la profondeur d'une queue SQS).

Les trois derniers types demandent un **adaptateur de métriques**
personnalisé (le plus courant : `prometheus-adapter`, qui expose des
métriques Prometheus via l'API `custom.metrics.k8s.io`) — `metrics-server`
seul ne fournit que CPU/mémoire. C'est exactement ce qu'il faudrait pour
le serveur d'inférence BentoML esquissé plus tôt : scaler sur le nombre
de requêtes/seconde ou la latency p99 plutôt que sur le CPU, en
branchant son endpoint `/metrics` à Prometheus puis Prometheus à
`prometheus-adapter`.

## Et la mémoire, les nœuds ?

Mentionné pour la carte mentale, pas implémenté ici :

- **VerticalPodAutoscaler (VPA)** : au lieu de changer le *nombre* de
  Pods, ajuste leurs `requests`/`limits` CPU/mémoire — complémentaire au
  HPA (en pratique, les deux en même temps sur la *même* métrique CPU
  sont déconseillés, ils se marchent sur les pieds).
- **Cluster Autoscaler** : ajoute/retire des **nœuds** quand les Pods ne
  trouvent plus de place à scheduler — un niveau au-dessus du HPA (qui
  ne crée jamais de nœud, juste des Pods, qui peuvent rester `Pending`
  si le cluster est plein).

## Nettoyer

```bash
kubectl delete deployment load-generator -n tutorial-app 2>/dev/null
helm uninstall tuto -n tutorial-app
minikube delete
```

---

Fin du tutoriel. En partant d'une simple image Docker, on a traversé :

Pod → ReplicaSet → Deployment → Service → Namespace → ConfigMap →
Secret → PersistentVolume → StatefulSet → Ingress → Helm → RBAC →
HorizontalPodAutoscaler

— les briques qu'on retrouve dans la quasi-totalité des applications
tournant sur Kubernetes en production, y compris dans des stacks bien
plus riches (voir l'esquisse de plateforme ML : MLflow, Postgres,
MinIO, BentoML, Prometheus/Grafana, Airflow — chacun de ses morceaux se
ramène à un sous-ensemble de ce qu'on vient de pratiquer ici).
