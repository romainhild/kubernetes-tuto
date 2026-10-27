# Étape 9 — Le StatefulSet

À l'étape 8, Postgres tournait dans un Deployment classique, volontairement
limité à 1 réplique, avec une stratégie `Recreate` pour contourner le
problème du volume `ReadWriteOnce` partagé. Un **StatefulSet** est fait
spécifiquement pour ce genre de charge : il donne à chaque Pod une
**identité stable** et **son propre volume**, et gère les mises à jour
dans l'ordre sans le hack `Recreate`.

## Ce qui change

- `k8s/postgres-deployment.yaml` et `k8s/postgres-pvc.yaml` disparaissent,
  remplacés par `k8s/postgres-statefulset.yaml`.
- `k8s/postgres-service.yaml` devient **headless** (`clusterIP: None`) :
  c'est le Service "gouvernant" référencé par `serviceName` dans le
  StatefulSet.
- `k8s/db-config.yaml` : `DB_HOST` passe de `postgres` à
  `postgres-0.postgres` — explication plus bas, c'est le cœur de la leçon.

## Les trois garanties d'un StatefulSet

1. **Noms stables et ordonnés** : les Pods s'appellent `postgres-0`,
   `postgres-1`, ... (pas de suffixe aléatoire comme un Deployment), créés
   dans l'ordre (`0` doit être `Ready` avant que `1` démarre), et détruits
   dans l'ordre inverse en cas de scale-down.
2. **Un volume dédié par Pod, qui le suit** : `volumeClaimTemplates`
   génère un PVC par réplique, nommé `<template>-<statefulset>-<n>`. Si
   `postgres-1` est supprimé puis recréé, il **retrouve son propre PVC**
   (pas un volume neuf, et pas celui de `postgres-0`).
3. **DNS stable par Pod** : grâce au Service headless `postgres`, chaque
   Pod est joignable individuellement via
   `<pod>.<service>.<namespace>.svc.cluster.local`, ex:
   `postgres-0.postgres.tutorial-app.svc.cluster.local` (raccourci en
   `postgres-0.postgres` depuis le même namespace).

## Essayer

```bash
kubectl apply -f k8s/postgres-service.yaml -f k8s/postgres-statefulset.yaml
kubectl get pods -n tutorial-app -l app=postgres -w
```

Observe `postgres-0` passer `Running`/`Ready` avant que `postgres-1`
démarre seulement ensuite — un ReplicaSet aurait lancé les deux en
parallèle.

```bash
kubectl get pvc -n tutorial-app
```

Deux PVC distincts : `postgres-data-postgres-0` et
`postgres-data-postgres-1`.

## Le piège à bien comprendre : scaler ≠ répliquer les données

```bash
kubectl exec -n tutorial-app postgres-0 -- psql -U tutorial_user -d tutorial -c \
  "CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY); INSERT INTO visits DEFAULT VALUES; SELECT count(*) FROM visits;"

kubectl exec -n tutorial-app postgres-1 -- psql -U tutorial_user -d tutorial -c \
  "CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY); SELECT count(*) FROM visits;"
```

`postgres-1` affiche `0`, pas le compte de `postgres-0`. **Chaque Pod a
sa propre base de données, totalement indépendante**, avec son propre
disque vide au démarrage. Un StatefulSet donne la *mécanique* (identité,
stockage stable) pour faire tourner un système distribué avec état, mais
il **n'implémente aucune réplication** : vanille Postgres ne sait pas se
synchroniser tout seul entre plusieurs Pods. Pour une vraie HA Postgres
sur Kubernetes, on s'appuie sur un opérateur dédié qui configure la
réplication en streaming et l'élection du primaire (CloudNativePG,
Zalando postgres-operator, Patroni...) — un StatefulSet est la fondation
sur laquelle ces opérateurs sont construits, pas un remplaçant.

C'est exactement pour ça que `k8s/db-config.yaml` pointe explicitement
sur `postgres-0.postgres` plutôt que sur le Service `postgres` : si
l'appli se connectait au nom du Service headless, la résolution DNS
renverrait les IP des **deux** Pods, et selon lequel le client choisit,
elle verrait tantôt une base, tantôt l'autre — un bug d'incohérence
silencieux. En pointant sur le Pod `-0` explicitement, on garde une
unique source de vérité, comme avant.

Applique le changement de ConfigMap à l'appli :

```bash
kubectl apply -f k8s/db-config.yaml
kubectl rollout restart deployment/web -n tutorial-app
kubectl port-forward -n tutorial-app service/web 8080:80
```

## Mise à jour et scale-down ordonnés

```bash
kubectl scale statefulset postgres --replicas=1 -n tutorial-app
kubectl get pods -n tutorial-app -l app=postgres
kubectl get pvc -n tutorial-app
```

`postgres-1` (le plus grand ordinal) est supprimé en premier — et son
PVC **reste présent** : par défaut, un StatefulSet ne supprime jamais
les PVC de ses `volumeClaimTemplates`, ni au scale-down ni même si tu
supprimes le StatefulSet entier (c'est volontaire, pour ne jamais perdre
des données par accident). Il faut les supprimer explicitement :

```bash
kubectl delete pvc postgres-data-postgres-1 -n tutorial-app
```

(Note : depuis Kubernetes 1.27, le champ
`spec.persistentVolumeClaimRetentionPolicy` permet de changer ce
comportement par défaut — `whenScaled`/`whenDeleted` à `Delete` au lieu
de `Retain` — mais `Retain` reste le défaut, par sécurité.)

Remets 2 répliques pour la suite si tu veux, ou reste à 1 — la ConfigMap
pointe toujours sur `postgres-0`, qui existe dans les deux cas.

```bash
kubectl scale statefulset postgres --replicas=2 -n tutorial-app
```

## Étape suivante

```bash
git checkout step-10-ingress
cat STEP.md
```

On arrête d'utiliser `kubectl port-forward` pour de bon : place à
l'**Ingress**, pour exposer l'appli sur un vrai nom d'hôte.
