# Étape 1 — Le Pod

Un **Pod** est la plus petite unité que Kubernetes sait déployer. Ce n'est
pas directement "un conteneur" : c'est une enveloppe qui peut contenir un
ou plusieurs conteneurs qui partagent le même réseau (même IP, mêmes
ports) et peuvent partager des volumes. Dans l'immense majorité des cas on
met un seul conteneur "principal" par Pod, et on ajoute un deuxième
conteneur seulement pour un rôle d'accompagnement (un "sidecar" : proxy,
agent de logs, synchronisation de fichiers...).

## Nouveau fichier

- `k8s/pod.yaml` — décrit un Pod nommé `web`, basé sur notre image Docker
  de l'étape 0, qui écoute sur le port 80.

## Rendre l'image disponible à minikube

minikube tourne dans sa propre VM/conteneur, avec son propre daemon
Docker — il ne voit pas les images de ton Docker local. Il faut donc lui
donner l'image explicitement :

```bash
minikube image build -t local/k8s-tutorial-web:dev app/
```

C'est pour ça que le Pod utilise `imagePullPolicy: Never` : on dit à
Kubernetes "ne va jamais chercher cette image sur un registry, elle est
déjà là en local".

(Alternative possible : `eval $(minikube docker-env)` puis un `docker
build` classique — ça bascule ton terminal pour pointer vers le daemon
Docker de minikube.)

## Essayer

```bash
kubectl apply -f k8s/pod.yaml
kubectl get pods
kubectl describe pod web
```

Accéder à la page (minikube n'expose rien automatiquement, on fait un
tunnel local vers le Pod) :

```bash
kubectl port-forward pod/web 8080:80
```

Ouvrir http://localhost:8080 dans un autre terminal.

Voir les logs du conteneur du Pod :

```bash
kubectl logs web
```

## Le point important : un Pod ne se répare pas tout seul

```bash
kubectl delete pod web
kubectl get pods
```

Le Pod a disparu, point final. Rien ne le recrée. C'est normal : un Pod
seul n'a aucune notion de "combien d'instances je veux" ni de
"relance-le s'il meurt". C'est tout l'objet de la prochaine étape.

En pratique, on crée donc **très rarement** des Pods à la main comme on
vient de le faire — c'est surtout utile pour du debug ponctuel
(`kubectl run debug --image=busybox -it --rm -- sh`). Pour une vraie
appli, on passe par un contrôleur qui gère des Pods pour nous.

## Étape suivante

```bash
git checkout step-2-replicaset
cat STEP.md
```

On introduit le **ReplicaSet**, qui garantit qu'un certain nombre de
copies du Pod tournent en permanence.
