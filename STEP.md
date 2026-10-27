# Étape 10 — L'Ingress

Jusqu'ici, pour atteindre l'appli depuis ton navigateur, il fallait soit
`kubectl port-forward` (un tunnel qui ne survit pas à la fermeture du
terminal), soit un Service `NodePort`/`LoadBalancer` (un port par
service, pas de nom de domaine, pas de routage par chemin). Un
**Ingress** résout le problème de "comment exposer plusieurs
applications HTTP(S) proprement, avec de vrais noms d'hôte et des
chemins, derrière une seule entrée" — exactement ce qu'un reverse proxy
fait devant un parc de services.

## Point essentiel à comprendre tout de suite

**Une ressource `Ingress` seule ne fait rien.** Contrairement à un
Service (que `kube-proxy` implémente nativement sur chaque nœud),
l'Ingress n'est qu'un ensemble de règles ("si host=X et path=Y, envoie
vers ce Service"). Il faut un **Ingress Controller** — un vrai
reverse proxy qui tourne dans le cluster (sous forme de Pods, comme
n'importe quelle appli) et qui surveille les objets Ingress pour
configurer son routage. Sans controller, créer un Ingress ne change
absolument rien. Les plus courants : ingress-nginx, Traefik, HAProxy,
ou des versions managées par les clouds (ALB sur AWS, GCE sur GCP...).

## Activer un Ingress Controller sur minikube

```bash
minikube addons enable ingress
kubectl get pods -n ingress-nginx
```

Ça déploie `ingress-nginx` (basé sur nginx) dans son propre namespace.
Attends que le Pod du controller soit `Running`.

## Nouveaux fichiers

- `k8s/ingress.yaml` — route `http://tuto.local/` vers le Service `web`.
- `k8s/ingress-tls.yaml` — la même chose, en HTTPS (section plus bas).

## Essayer

```bash
kubectl apply -f k8s/ingress.yaml
kubectl get ingress -n tutorial-app
```

La colonne `CLASS` doit afficher `nginx`, et `ADDRESS` finira par se
remplir avec l'IP du controller.

### Accéder à l'appli via un vrai nom d'hôte

Deux choses à faire : dire à ton Mac que `tuto.local` doit pointer vers
le controller, puis rendre le controller joignable depuis ton poste.

**1. Résoudre `tuto.local` vers ta machine** (nécessite `sudo`, une
seule fois) :

```bash
echo "127.0.0.1 tuto.local" | sudo tee -a /etc/hosts
```

**2. Exposer le controller sur ton poste** — avec le driver Docker de
minikube sur Mac, l'IP du nœud n'est pas directement joignable depuis
le Mac, donc on fait un port-forward vers le Service du controller
(le même mécanisme que pour nos propres apps aux étapes précédentes,
appliqué cette fois au reverse proxy plutôt qu'à `web` directement) :

```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80 8443:443
```

Puis dans un navigateur ou avec curl :

```bash
curl http://tuto.local:8080/
```

Tu dois voir la page de l'appli — en passant cette fois par
`tuto.local` → ingress-nginx → Service `web` → un des Pods, et plus par
un port-forward direct sur l'appli.

(Alternative, plus proche d'un vrai port 80/443 : `minikube tunnel`
dans un terminal séparé — laissé ouvert, demande aussi `sudo` — puis
`http://tuto.local` sans port. Le port-forward ci-dessus évite ce
`sudo` supplémentaire et marche de façon identique pour apprendre.)

## HTTPS avec un certificat auto-signé

On génère un certificat auto-signé (ne jamais faire ça pour un vrai
site public — un navigateur affichera un avertissement, normal) :

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /tmp/tuto.key -out /tmp/tuto.crt -subj "/CN=tuto.local"

kubectl create secret tls tuto-tls \
  --cert=/tmp/tuto.crt --key=/tmp/tuto.key \
  -n tutorial-app
```

Tu reconnais `kubectl create secret tls` : c'est le type
`kubernetes.io/tls` vu à l'étape 7, avec ses clés obligatoires
`tls.crt`/`tls.key`.

```bash
kubectl apply -f k8s/ingress-tls.yaml
curl -k https://tuto.local:8443/
```

Le `-k` dit à curl d'ignorer l'avertissement de certificat auto-signé
(un vrai site utiliserait un certificat signé par une autorité reconnue,
ex: via cert-manager + Let's Encrypt — hors du cadre de ce tuto).

## Les options de routage

- **`pathType`** :
  - `Prefix` (notre cas) : `/` matche tout.
  - `Exact` : doit correspondre caractère pour caractère.
  - `ImplementationSpecific` : laissé à l'interprétation du controller.
- **Plusieurs chemins vers des services différents** (fan-out), pour
  exposer plusieurs applications sous le même host :
  ```yaml
  rules:
    - host: tuto.local
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend: { service: { name: api, port: { number: 80 } } }
          - path: /
            pathType: Prefix
            backend: { service: { name: web, port: { number: 80 } } }
  ```
- **Plusieurs hosts** dans le même Ingress, chacun avec ses propres
  règles — pratique pour héberger plusieurs sites derrière un seul
  controller/une seule IP publique.
- **`ingressClassName`** : un cluster peut avoir plusieurs controllers
  installés (`kubectl get ingressclass` les liste) ; ce champ dit lequel
  doit traiter cet Ingress.
- Beaucoup de comportements fins (rewrite d'URL, limitation de débit,
  authentification basique...) passent par des **annotations**
  spécifiques au controller (ex:
  `nginx.ingress.kubernetes.io/rewrite-target`) plutôt que par le champ
  `spec` standard, qui reste volontairement minimal.

## Étape suivante

```bash
git checkout step-11-helm
cat STEP.md
```

On a maintenant pas mal de fichiers YAML à gérer à la main. Dernière
étape : les empaqueter dans un **chart Helm**.
