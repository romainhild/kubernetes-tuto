# Étape 5 — Le Namespace

Jusqu'ici, tout ce qu'on a créé vivait dans le namespace `default`. Un
**Namespace** est une façon de partitionner un cluster : les noms de
ressources (Deployment, Service...) doivent être uniques *dans* un
namespace, mais pas entre namespaces différents. Ça sert à isoler des
environnements (dev/staging/prod), des équipes, ou simplement à garder
un cluster personnel bien rangé.

Attention : **tout n'est pas namespacé**. Les Namespaces eux-mêmes, les
Nodes, les PersistentVolumes (pas les PVC !), ou les ClusterRoles sont
des ressources *cluster-wide*. La commande `kubectl api-resources
--namespaced=true` liste ce qui est namespacé ou pas.

## Nouveau fichier

- `k8s/namespace.yaml` — crée le namespace `tutorial-app`.

Et les fichiers existants ont tous reçu `namespace: tutorial-app` dans
leur `metadata` (`deployment.yaml`, `service-clusterip.yaml` et les
variantes de l'étape précédente).

## Nettoyer l'étape précédente et repartir dans le bon namespace

Si tu as encore les ressources de l'étape 4 dans `default` :

```bash
kubectl delete deployment web
kubectl delete service web
```

Puis :

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml -f k8s/service-clusterip.yaml
kubectl get all -n tutorial-app
```

Pratique pour ne plus taper `-n tutorial-app` à chaque commande, pendant
toute la suite du tutoriel :

```bash
kubectl config set-context --current --namespace=tutorial-app
kubectl get pods   # plus besoin de -n
```

(Pour revenir au namespace par défaut : `kubectl config set-context
--current --namespace=default`.)

## DNS entre namespaces

Un Service est joignable depuis n'importe quel namespace via son nom
complet : `<service>.<namespace>.svc.cluster.local` (souvent raccourci en
`<service>.<namespace>`). Depuis un Pod du même namespace, le simple nom
`web` suffit déjà (comme utilisé à l'étape 4).

## Limiter les ressources d'un namespace (pour info, pas appliqué ici)

Deux objets qu'on croise souvent en vrai, pour éviter qu'un namespace
épuise tout le cluster :

- **`ResourceQuota`** : plafonne le total de CPU/mémoire/nombre d'objets
  pour tout le namespace.
- **`LimitRange`** : impose des valeurs par défaut ou des bornes
  (min/max) de CPU/mémoire *par Pod/conteneur* dans le namespace.

On ne les configure pas dans ce tuto pour rester focalisé, mais c'est le
genre de chose qu'un cluster partagé en entreprise impose presque
toujours.

## Étape suivante

```bash
git checkout step-6-configmap
cat STEP.md
```
