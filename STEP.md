# Étape 11 — Helm

On a maintenant une dizaine de fichiers YAML à appliquer dans le bon
ordre, avec des valeurs répétées à la main entre les étapes (le nom du
namespace, le tag d'image, le message d'accueil...). **Helm** est le
gestionnaire de paquets de l'écosystème Kubernetes : il transforme ces
manifestes en un **chart** templatisé, paramétrable par un seul fichier
de valeurs, installable/désinstallable/mettable à jour comme un paquet.

Pré-requis : `brew install helm`.

## Ce qui change

On arrête d'utiliser `k8s/*.yaml` à partir de cette étape : tout est
remplacé par `chart/`, qui contient la même appli (ConfigMap, Secret,
StatefulSet Postgres, Service headless, Deployment, Service, Ingress)
sous forme de templates. Rien n'est perdu : chaque étape précédente
reste consultable sur sa branche avec ses manifestes bruts — c'est tout
l'intérêt d'avoir fait ce tuto avec une branche par étape.

## Anatomie du chart

```
chart/
├── Chart.yaml        # métadonnées : nom, version du chart, version de l'appli
├── values.yaml        # les valeurs par défaut, le seul fichier que tu modifies en usage normal
├── .helmignore         # fichiers à ignorer lors du packaging (comme un .gitignore)
└── templates/
    ├── configmap.yaml
    ├── secret.yaml
    ├── postgres-service.yaml
    ├── postgres-statefulset.yaml
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    └── NOTES.txt      # affiché après install/upgrade, généré avec les valeurs utilisées
```

Chaque fichier sous `templates/` est un manifeste Kubernetes presque
normal, où certaines valeurs sont remplacées par des expressions
`{{ .Values.xxx }}` — regarde `chart/templates/deployment.yaml` : au
lieu de `image: local/k8s-tutorial-counter:dev` en dur, on a
`image: "{{ .Values.web.image.repository }}:{{ .Values.web.image.tag }}"`,
dont les valeurs viennent de `chart/values.yaml`.

Remarque : aucun fichier ne définit de Namespace, et aucun ne met de
champ `namespace:` — avec Helm, c'est `--namespace` (+
`--create-namespace` pour le créer s'il n'existe pas) qui s'en occupe à
l'installation, pour tout le chart d'un coup.

## Explorer sans rien installer

```bash
helm lint chart/
helm template tuto chart/ --namespace tutorial-app
```

`template` affiche le YAML final généré, exactement ce que `kubectl
apply` recevrait — très utile pour vérifier ce qu'un changement de
valeur va produire avant de l'appliquer pour de vrai.

## Installer

Un "Release" est une instance nommée d'un chart installée dans un
cluster (tu peux installer le même chart plusieurs fois, sous des noms
différents, par exemple pour plusieurs environnements).

> Si tu as encore les ressources des étapes précédentes dans
> `tutorial-app` (namespace, ConfigMap `db-config` nommée pareil,
> etc.), supprime-les d'abord pour éviter les conflits de noms :
> `kubectl delete all,configmap,secret,pvc,ingress -n tutorial-app --all`
> (le namespace lui-même peut rester, Helm s'en sert directement).

```bash
helm install tuto chart/ --namespace tutorial-app --create-namespace
kubectl get all -n tutorial-app
```

Lis les `NOTES` affichées à la fin : c'est `chart/templates/NOTES.txt`,
lui aussi templatisé.

```bash
helm list -n tutorial-app
helm status tuto -n tutorial-app
```

## Changer une valeur : `--set` ou un fichier de values

Pour un essai ponctuel :

```bash
helm upgrade tuto chart/ --namespace tutorial-app \
  --set web.welcomeMessage="Bonjour depuis une mise à jour Helm !" \
  --set web.replicaCount=5
kubectl get pods -n tutorial-app -l app=web
```

Observe : c'est un vrai `Deployment` qui reçoit ces changements, donc le
même rolling update que vu à l'étape 3 se déclenche.

Pour un usage durable (staging vs prod, par exemple), on préfère un
fichier de values dédié plutôt que des `--set` à rallonge :

```bash
cat > /tmp/values-demo.yaml <<'EOF'
web:
  replicaCount: 2
  welcomeMessage: "Valeurs depuis un fichier dédié"
EOF

helm upgrade tuto chart/ --namespace tutorial-app -f /tmp/values-demo.yaml
```

(Dans un vrai projet, ce fichier s'appellerait `values-staging.yaml`,
versionné à côté du chart, un par environnement.)

## Historique et rollback

```bash
helm history tuto -n tutorial-app
helm rollback tuto 1 -n tutorial-app
```

Chaque `install`/`upgrade` crée une révision numérotée ; `rollback`
revient à une révision précédente — le pendant Helm du `kubectl rollout
undo` vu à l'étape 3, mais au niveau de **tout le chart** d'un coup, pas
juste d'un Deployment.

## Désinstaller

```bash
helm uninstall tuto -n tutorial-app
```

Supprime toutes les ressources créées par le Release. Note : les PVC du
StatefulSet ne sont, comme vu à l'étape 9, pas forcément supprimés
automatiquement selon la politique de rétention — vérifie avec
`kubectl get pvc -n tutorial-app` après coup.

## Secrets et Helm — l'angle mort à connaître

`chart/values.yaml` contient `postgres.db.password` **en clair**. C'est
pratique pour ce tuto, mais ça veut dire que si tu commites ce fichier
dans un vrai projet, ton mot de passe de prod finit dans l'historique
Git — exactement le problème qu'on avait pointé à l'étape 7 à propos des
Secrets Kubernetes (le Secret, lui, protège l'accès dans le cluster ;
ça ne protège rien si la valeur est aussi écrite en clair dans ton repo
de charts). En pratique, les options courantes sont :

- ne jamais committer le fichier de values contenant les secrets, et le
  fournir à `helm install -f` depuis un endroit sécurisé (CI/CD avec
  secrets protégés, gestionnaire de secrets de l'organisation...),
- le plugin **`helm-secrets`** (chiffre un fichier de values entier avec
  SOPS/age/GPG, et le déchiffre à la volée au moment du `helm` command),
- un opérateur comme **External Secrets Operator** qui injecte les
  Secrets Kubernetes directement depuis Vault/AWS Secrets Manager/etc.,
  sans jamais les faire transiter par un fichier de values.

## Pour aller plus loin

- **Sub-charts/dépendances** (`Chart.yaml` → `dependencies:`) : composer
  plusieurs charts ensemble (ex: ton appli + le chart officiel
  `bitnami/postgresql` au lieu d'écrire le StatefulSet à la main).
- **Hooks** (`helm.sh/hook: pre-install`, `post-upgrade`...) : exécuter
  un Job avant/après une opération (ex: migration de base de données).
- **`helm package`** + un dépôt de charts (ChartMuseum, OCI registry...)
  pour distribuer un chart versionné à d'autres équipes.

## Étape suivante

```bash
git checkout step-12-rbac
cat STEP.md
```

On a maintenant un chart propre pour déployer l'appli. Reste deux
sujets qui reviennent dès qu'une appli a besoin de parler à l'API
Kubernetes elle-même, ou de scaler automatiquement : **RBAC**, puis le
**HorizontalPodAutoscaler**.
