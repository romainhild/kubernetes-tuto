# Étape 12 — RBAC

Jusqu'ici, nos Pods ne parlaient qu'à Postgres. Beaucoup d'applis réelles
ont besoin d'appeler l'**API Kubernetes elle-même** (lister des Pods,
lire une ConfigMap, créer un Job comme dans l'exemple Airflow qu'on a
esquissé...). **RBAC** (Role-Based Access Control) contrôle qui a le
droit de faire quoi sur l'API — "qui" pouvant être un humain, mais aussi
un Pod.

## Nouveau dans l'appli

L'appli expose maintenant un troisième morceau d'info sur sa page : elle
interroge l'API Kubernetes pour lister les autres Pods portant le label
`app=web` (voir `get_peer_info()` dans `app/counter/app.py`, via le
client Python officiel `kubernetes`). C'est exactement le genre d'appel
qui déclenche RBAC.

(Détail au passage : l'appli doit savoir dans quel namespace elle tourne
pour filtrer les Pods. Plutôt que de le coder en dur, `chart/templates/deployment.yaml`
utilise la **Downward API** pour l'injecter automatiquement :
`valueFrom.fieldRef.fieldPath: metadata.namespace` — un Pod peut
toujours connaître ses propres métadonnées sans configuration
supplémentaire, où qu'il soit déployé.)

## Comment un Pod s'authentifie auprès de l'API

Par défaut, **chaque Pod** se voit automatiquement monter un token
appartenant à un **ServiceAccount** (celui du namespace nommé
`default` si tu n'en précises pas un), dans
`/var/run/secrets/kubernetes.io/serviceaccount/`. C'est ce que
`config.load_incluster_config()` lit côté client Python — c'est pour ça
que notre appli n'a besoin d'aucune URL/credentials codés en dur pour
parler à l'API : le token et l'adresse de l'API sont déjà là, injectés
par Kubernetes lui-même.

Avoir un token ne donne **aucune permission** par défaut (RBAC est
"deny by default") — il faut explicitement lier ce ServiceAccount à des
droits via un `RoleBinding`.

## Les 4 objets RBAC

- **`ServiceAccount`** : l'identité du Pod (`chart/templates/serviceaccount.yaml`,
  nommé `web`, référencé par `serviceAccountName: web` dans le
  Deployment).
- **`Role`** : une liste de permissions, **namespacée** — s'applique
  uniquement dans le namespace où elle est créée.
  (`chart/templates/rbac.yaml`, verbes `get`/`list`/`watch` sur les
  `pods`.)
- **`ClusterRole`** : la même chose, mais cluster-wide (ou pour des
  ressources elles-mêmes non-namespacées, comme `Node` ou `Namespace`).
  On n'en a pas besoin ici : notre appli n'a besoin de voir que les Pods
  de son propre namespace. Un controller comme `ingress-nginx` (étape
  10) ou un scraper Prometheus qui découvre des cibles dans tout le
  cluster, eux, ont besoin d'un ClusterRole.
- **`RoleBinding`** / **`ClusterRoleBinding`** : relie un Role/ClusterRole
  à un ou plusieurs "subjects" (`ServiceAccount`, `User`, ou `Group`).
  Sans binding, un Role ne s'applique à personne.

Règle simple : namespaced + namespaced (Role + RoleBinding) pour limiter
la portée au namespace ; ClusterRole peut être réutilisé par plusieurs
RoleBindings namespacés différents (pratique : un seul ClusterRole
"pod-reader" réutilisable, lié namespace par namespace) ou par un
ClusterRoleBinding pour une portée vraiment globale.

## Essayer

```bash
helm upgrade tuto chart/ --namespace tutorial-app
kubectl port-forward -n tutorial-app service/web 8080:80
curl -s http://localhost:8080/ | grep "API Kubernetes"
```

Tu dois voir la liste des Pods `web-xxxxx`.

Vérifie les objets créés :

```bash
kubectl get serviceaccount,role,rolebinding -n tutorial-app
kubectl describe role web-pod-reader -n tutorial-app
```

Et la commande la plus utile pour déboguer RBAC — simuler "est-ce que ce
ServiceAccount peut faire X" sans avoir à redéployer quoi que ce soit :

```bash
kubectl auth can-i list pods \
  --as=system:serviceaccount:tutorial-app:web -n tutorial-app
```

## Casser puis réparer

Le chart a un flag `rbac.create` justement pour ça :

```bash
helm upgrade tuto chart/ --namespace tutorial-app --set rbac.create=false
kubectl get role,rolebinding -n tutorial-app   # plus rien
curl -s http://localhost:8080/ | grep "API Kubernetes"
```

Le ServiceAccount `web` existe toujours (le Deployment le référence
toujours), mais sans Role ni RoleBinding, l'appel est refusé — tu
devrais voir le message "refusé par RBAC (HTTP 403)" généré par
`get_peer_info()`. Note que **l'appli ne crashe pas** : elle capture
l'erreur et l'affiche, exactement comme on gérerait un service externe
indisponible.

```bash
helm upgrade tuto chart/ --namespace tutorial-app --set rbac.create=true
```

(ou simplement ré-applique sans `--set`, `true` est la valeur par défaut
dans `values.yaml`.)

## Le principe du moindre privilège

Remarque ce qu'on **n'a pas** donné au Role : pas de `create`, pas de
`delete`, pas de `update`, pas d'accès aux `secrets` ou aux
`configmaps`, uniquement `get`/`list`/`watch` sur les `pods`. Une appli
ne devrait jamais avoir plus de droits que ce dont elle a réellement
besoin — un Pod compromis avec un ClusterRole `cluster-admin` serait une
porte ouverte vers tout le cluster, alors qu'un Pod compromis avec notre
Role n'expose au pire que la liste des noms de Pods du namespace.

Si un Pod n'a besoin d'appeler l'API Kubernetes pour rien du tout
(la plupart des cas), il vaut mieux désactiver complètement le montage
du token plutôt que de laisser le ServiceAccount `default` traîner :

```yaml
automountServiceAccountToken: false
```

(dans `spec.template.spec`, à côté de `serviceAccountName`.)

## Étape suivante

```bash
git checkout step-13-hpa
cat STEP.md
```

On vient d'ajouter un appel réseau par requête (vers l'API Kubernetes)
en plus de la base — bon prétexte pour parler de scaling automatique :
le **HorizontalPodAutoscaler**.
