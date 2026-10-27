# Étape 2 — Le ReplicaSet

Un **ReplicaSet** garantit qu'un nombre donné de Pods identiques (définis
par un `template`) tournent en permanence. Si un Pod meurt, est supprimé,
ou si le nœud qui l'hébergeait tombe, le ReplicaSet en recrée un nouveau
pour revenir au compte demandé (`replicas`).

Le lien entre le ReplicaSet et "ses" Pods se fait uniquement par
**labels** : le `selector.matchLabels` du ReplicaSet (`app: web`) doit
correspondre aux labels du `template`. C'est ce mécanisme de label/selector
qu'on va retrouver partout dans Kubernetes (Deployment, Service...).

## Nouveau fichier

- `k8s/replicaset.yaml` — remplace `k8s/pod.yaml`. Demande 3 réplicas du
  même Pod que l'étape précédente.

(Image toujours disponible dans minikube depuis l'étape 1 — si tu as
fait `minikube delete` entre-temps, relance `minikube image build -t
local/k8s-tutorial-web:dev app/`.)

## Essayer

```bash
kubectl apply -f k8s/replicaset.yaml
kubectl get replicaset
kubectl get pods -o wide --show-labels
```

Tu dois voir 3 Pods, tous avec le label `app=web`, nommés
`web-xxxxx` (suffixe aléatoire).

## Démonstration : l'auto-réparation

Supprime un des trois Pods (remplace par un nom réel de ta machine) :

```bash
kubectl delete pod web-<suffixe>
kubectl get pods -w
```

Un nouveau Pod apparaît presque immédiatement pour revenir à 3. C'est la
différence fondamentale avec l'étape 1.

## Démonstration : le scaling

```bash
kubectl scale replicaset web --replicas=5
kubectl get pods
kubectl scale replicaset web --replicas=2
kubectl get pods
```

## La limite du ReplicaSet

Essaie de changer quelque chose dans `app/index.html`, reconstruis
l'image avec le **même tag** (`local/k8s-tutorial-web:dev`), puis
réapplique le ReplicaSet : rien ne se passe, les Pods existants ne sont
pas recréés, car le ReplicaSet ne surveille que le *nombre* de Pods, pas
leur contenu. Pour changer la version qui tourne, il faudrait supprimer
les Pods à la main un par un (en gérant soi-même la bascule pour éviter
une coupure de service) — fastidieux et risqué.

C'est exactement le problème que le **Deployment** résout : il pilote un
(ou plusieurs) ReplicaSet(s) pour toi et sait faire des mises à jour
progressives sans interruption de service.

En pratique, comme pour le Pod, on crée très rarement un ReplicaSet
directement — on passe quasi systématiquement par un Deployment.

## Étape suivante

```bash
git checkout step-3-deployment
cat STEP.md
```
