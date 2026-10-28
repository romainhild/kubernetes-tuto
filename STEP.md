# Étape 8 — PersistentVolume, PersistentVolumeClaim, et une vraie base de données

Dernière couche : on remplace la page statique par une petite appli
Python (Flask) qui compte ses visites dans une base **Postgres**, et on
apprend comment Kubernetes gère le stockage qui doit **survivre** à la
suppression d'un Pod — ce qu'aucune des ressources vues jusqu'ici ne
permettait (un Pod recréé repart toujours de zéro).

## Vue d'ensemble de ce qui change

- Nouvelle appli : `app/counter/` (Flask + psycopg2), qui remplace
  `nginx` dans le Deployment `web`.
- `k8s/db-config.yaml` et `k8s/db-secret.yaml` remplacent
  `web-content`/`web-secret` : mêmes idées que les étapes 6 et 7, mais
  leurs clés sont maintenant **partagées entre deux Deployments**
  différents (l'appli et Postgres).
- `k8s/postgres-pvc.yaml`, `k8s/postgres-deployment.yaml`,
  `k8s/postgres-service.yaml` : la base de données elle-même.
- `k8s/deployment.yaml` : le Deployment `web` utilise maintenant l'image
  du compteur et se connecte à Postgres.

## PersistentVolume, PersistentVolumeClaim, StorageClass : qui fait quoi

Trois objets différents, souvent confondus :

- **`PersistentVolume` (PV)** : un morceau de stockage réel (un disque,
  un export NFS, un hostPath...), une ressource *cluster-wide* (pas dans
  un namespace). Quelqu'un (un admin, ou un provisioner automatique) doit
  le créer.
- **`PersistentVolumeClaim` (PVC)** : une **demande** de stockage faite
  par un utilisateur/une appli ("je veux 1Gi, en ReadWriteOnce"). C'est
  namespacé, et c'est ce qu'on référence depuis un Pod.
- **`StorageClass`** : un "profil" qui dit *comment* provisionner un PV
  automatiquement quand un PVC le demande (quel type de disque, quel
  driver...). C'est le **provisioning dynamique** : plus besoin de créer
  les PV à la main, le cluster le fait dès qu'un PVC apparaît.

Dans ce tuto on ne crée aucun PV ni StorageClass : minikube a déjà une
StorageClass par défaut (`standard`, basée sur `hostPath`) qui
provisionne automatiquement un PV dès que `k8s/postgres-pvc.yaml` est
appliqué. C'est le cas le plus courant en pratique.

```bash
kubectl apply -f k8s/postgres-pvc.yaml
kubectl get pvc -n tutorial-app
kubectl get pv
```

Tu verras le PVC passer en `Bound`, lié à un PV créé automatiquement.

## Les Access Modes

- **`ReadWriteOnce` (RWO)** : monté en lecture/écriture par **un seul
  nœud** à la fois (pas "un seul Pod" strictement — plusieurs Pods sur
  le même nœud peuvent le partager, mais c'est rare en pratique). C'est
  le mode qu'on utilise ici pour Postgres, et le plus répandu
  (disques cloud classiques : EBS, Persistent Disk...).
- **`ReadOnlyMany` (ROX)** : plusieurs nœuds en lecture seule.
- **`ReadWriteMany` (RWX)** : plusieurs nœuds en lecture/écriture —
  demande un backend qui le supporte vraiment (NFS, EFS, Filestore...),
  pas les disques blocs classiques.

## Pourquoi `strategy: Recreate` sur le Deployment Postgres

Regarde `k8s/postgres-deployment.yaml` : contrairement au Deployment
`web`, sa stratégie est `Recreate`, pas `RollingUpdate`. Avec un volume
`ReadWriteOnce`, un rolling update voudrait démarrer le nouveau Pod
*avant* de couper l'ancien — mais le nouveau Pod resterait bloqué en
`Pending`, incapable de monter un volume déjà attaché à l'ancien Pod.
`Recreate` supprime l'ancien avant de créer le nouveau : une courte
coupure, mais pas de blocage.

(Note au passage : `PGDATA` est réglé sur un sous-dossier
`/var/lib/postgresql/data/pgdata` plutôt que la racine du volume monté —
certains backends de volume y créent un dossier `lost+found` que
Postgres refuse de voir à la racine de son data dir.)

## Construire et déployer

```bash
minikube image build -t local/k8s-tutorial-counter:dev app/counter/

kubectl apply -f k8s/db-config.yaml -f k8s/db-secret.yaml
kubectl apply -f k8s/postgres-pvc.yaml -f k8s/postgres-deployment.yaml -f k8s/postgres-service.yaml
kubectl rollout status deployment/postgres -n tutorial-app

kubectl apply -f k8s/deployment.yaml -f k8s/service-clusterip.yaml
kubectl rollout status deployment/web -n tutorial-app
```

(On démarre Postgres avant l'appli : l'appli retente la connexion
pendant 20 secondes si la base n'est pas encore prête, mais ce n'est
qu'un filet de sécurité — en vrai on utiliserait plutôt un **init
container** qui attend explicitement que la base soit joignable avant
de démarrer le conteneur principal.)

```bash
kubectl port-forward -n tutorial-app service/web 8080:80
```

Rafraîchis http://localhost:8080 plusieurs fois : le compteur
augmente, et le nom du Pod qui répond change (3 réplicas de `web`
derrière le même Service) — mais le compteur, lui, reste cohérent,
puisqu'il vit dans Postgres, pas dans le Pod.

## Démonstration : la persistance, pour de vrai

```bash
kubectl delete pod -n tutorial-app -l app=postgres
kubectl get pods -n tutorial-app -w
```

Un nouveau Pod Postgres est recréé (comme à l'étape 2 pour `web`). Une
fois prêt, recharge la page : **le compteur n'a pas été remis à zéro**.
Les données vivent dans le PV, pas dans le Pod — c'est tout l'objet de
cette étape.

Compare avec la suppression du PVC lui-même :

```bash
kubectl delete -f k8s/postgres-deployment.yaml
kubectl delete pvc postgres-data -n tutorial-app
kubectl apply -f k8s/postgres-pvc.yaml -f k8s/postgres-deployment.yaml
```

Cette fois un **nouveau** PV est provisionné vide : le compteur repart
de zéro. La règle est : le cycle de vie du **stockage** suit le PVC, pas
le Pod — supprimer le PVC (ou son PV) supprime les données.

## Reclaim Policy

Quand un PVC est supprimé, que devient le PV sous-jacent ?

- **`Delete`** (par défaut avec la plupart des provisioners dynamiques,
  dont celui de minikube) : le PV et le stockage physique sont détruits.
- **`Retain`** : le PV reste, à l'état `Released`, données intactes,
  mais il faut une intervention manuelle pour le réutiliser.

```bash
kubectl get pv -o custom-columns=NAME:.metadata.name,RECLAIM:.spec.persistentVolumeReclaimPolicy
```

## Et pour plusieurs répliques de base de données ?

Une seule instance Postgres avec un Deployment classique, comme ici,
est volontairement simplifié. Pour répliquer une base de données (ou
tout système où chaque instance a une identité et un stockage propres),
Kubernetes a une ressource dédiée : le **StatefulSet**. Contrairement à
un Deployment, chaque Pod d'un StatefulSet garde un nom stable
(`postgres-0`, `postgres-1`...) et **son propre** PVC, recréé
automatiquement avec le même nom à chaque redémarrage — généralement
combiné à un Service headless (vu à l'étape 4) pour que chaque instance
soit adressable individuellement. Hors du cadre de ce tuto, mais c'est
la suite logique si tu veux creuser.

## Étape suivante

```bash
git checkout step-9-statefulset
cat STEP.md
```

On vient de limiter Postgres à 1 réplique pour éviter les complications
d'un Deployment classique sur un volume partagé. L'étape suivante
introduit la ressource faite pour ça : le **StatefulSet**.
