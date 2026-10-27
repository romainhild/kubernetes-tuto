# Étape 4 — Le Service

Jusqu'ici on accédait à l'appli via `kubectl port-forward`, pratique pour
débugger mais pas pour un usage réel : ça ouvre un tunnel depuis TON
poste vers UN Pod précis, qui disparaît si ce Pod est recréé.

Un **Service** résout deux problèmes à la fois :
1. **Découverte** : donner un nom stable (DNS interne) à un ensemble de
   Pods qui changent tout le temps (recréés, scalés, mis à jour...).
2. **Répartition de charge** : le trafic envoyé au Service est réparti
   entre tous les Pods qui matchent son `selector` et sont "Ready"
   (souviens-toi des `readinessProbe` de l'étape précédente — c'est
   exactement là qu'elles servent).

Le lien Service → Pods se fait, comme pour le ReplicaSet, uniquement par
labels (`selector: app: web`), jamais par nom de Pod.

## Les fichiers de cette étape

- `k8s/service-clusterip.yaml` — **celui qu'on applique par défaut**.
- `k8s/service-nodeport.yaml`, `k8s/service-loadbalancer.yaml`,
  `k8s/service-headless.yaml`, `k8s/service-externalname.yaml` — les
  autres types, à essayer en option (expliqués ci-dessous), en plus du
  ClusterIP (noms différents, donc pas de conflit).

## Les types de Service

### `ClusterIP` (par défaut)

Une IP virtuelle, stable, **routable uniquement depuis l'intérieur du
cluster**. C'est le bon choix pour la communication entre services
internes (ex: une appli qui parle à sa base de données — on l'utilisera
à l'étape 8).

```bash
kubectl apply -f k8s/service-clusterip.yaml
kubectl get service web
kubectl run curler --rm -it --image=busybox --restart=Never -- wget -qO- http://web
```

Et toujours accessible depuis ton poste via port-forward, mais cette
fois sur le Service plutôt que sur un Pod précis (le Service survit à
la recréation des Pods, pas le port-forward sur un Pod) :

```bash
kubectl port-forward service/web 8080:80
```

### `NodePort`

En plus d'un ClusterIP, ouvre le **même port sur chaque nœud** du
cluster (ici `30080`, dans la plage autorisée 30000-32767). N'importe
qui qui peut atteindre un nœud peut atteindre le Service.

```bash
kubectl apply -f k8s/service-nodeport.yaml
minikube service web-nodeport --url
```

### `LoadBalancer`

Dans un vrai cloud (AWS/GCP/Azure/OVH...), ce type déclenche la création
automatique d'un load balancer externe avec une IP publique — c'est le
mécanisme derrière "exposer une appli sur Internet" en prod. En local,
minikube simule ça avec `minikube tunnel` :

```bash
kubectl apply -f k8s/service-loadbalancer.yaml
minikube tunnel   # terminal à part, à laisser ouvert
kubectl get service web-loadbalancer   # observe l'EXTERNAL-IP apparaître
```

### `ClusterIP: None` (Service headless)

Pas d'IP virtuelle : une requête DNS sur le nom du Service renvoie
directement les IP de tous les Pods. Utile quand le client doit gérer
lui-même la connexion à un Pod précis (bases de données répliquées,
certains protocoles). On en reparlera avec les StatefulSets à l'étape 8.

### `ExternalName`

Pas de Pods, pas de selector : un simple alias DNS interne vers un nom
externe. Sert à appeler une dépendance externe par un nom "interne"
stable, pratique si l'adresse réelle change plus tard.

## Nettoyage avant de passer à l'étape suivante

```bash
kubectl delete service web-nodeport web-loadbalancer web-headless 2>/dev/null
```

(On garde le Deployment et le Service `web` en ClusterIP pour la suite.)

## Étape suivante

```bash
git checkout step-5-namespace
cat STEP.md
```
