# Étape 7 — Le Secret

Un **Secret** ressemble énormément à un ConfigMap (même structure, même
façon de le consommer en env var ou en volume) — mais il existe une
différence de fond à bien comprendre tout de suite :

> **Un Secret n'est PAS chiffré par défaut.** Ses valeurs sont juste
> encodées en base64 dans etcd (la base de données du cluster) — le
> base64 est un encodage, pas un chiffrement, n'importe qui peut le
> décoder instantanément. La vraie protection vient d'ailleurs :
> - le chiffrement au repos dans etcd doit être activé explicitement par
>   l'administrateur du cluster (`--encryption-provider-config`),
> - et le RBAC doit restreindre qui a le droit de lire les Secrets
>   (`get`/`list` sur la ressource `secrets`).
>
> Dans beaucoup d'organisations, les vrais secrets de prod ne sont de
> toute façon pas stockés en clair dans un manifeste Kubernetes, mais
> injectés depuis un gestionnaire externe (Vault, AWS Secrets Manager,
> Sealed Secrets, External Secrets Operator...).

## Nouveau fichier

- `k8s/secret.yaml` — un Secret `Opaque` (le type "générique", pour une
  donnée sans structure particulière) contenant un faux token d'API.

On utilise ici `stringData` plutôt que `data` : avec `stringData`, tu
écris la valeur en clair dans le YAML et Kubernetes l'encode en base64
pour toi au moment de la création. Avec `data`, tu dois fournir toi-même
la valeur déjà encodée (`echo -n "valeur" | base64`). `stringData` est
en écriture seule — en relisant le Secret (`kubectl get secret ... -o
yaml`), tu verras toujours la version encodée sous `data`.

Et `k8s/deployment.yaml` consomme ce Secret exactement comme la
ConfigMap, via `secretKeyRef` :

```yaml
- name: API_TOKEN
  valueFrom:
    secretKeyRef:
      name: web-secret
      key: API_TOKEN
```

## Essayer

```bash
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/web -n tutorial-app
```

Regarde le Secret tel que stocké :

```bash
kubectl get secret web-secret -n tutorial-app -o yaml
```

La valeur apparaît encodée en base64. Décode-la pour constater qu'il
n'y a aucune protection cryptographique :

```bash
kubectl get secret web-secret -n tutorial-app -o jsonpath='{.data.API_TOKEN}' | base64 -d
```

Et vérifie que le Pod a bien reçu la valeur en clair en variable d'env
(c'est le conteneur qui la voit en clair, le chiffrement/RBAC protège
l'accès *au Secret lui-même*, pas son utilisation dans le Pod) :

```bash
kubectl exec -n tutorial-app deploy/web -- env | grep API_TOKEN
```

## Les autres types de Secret

Le `type` d'un Secret ne change pas le stockage (toujours juste du
base64), mais aide Kubernetes et les outils à valider sa structure :

- **`Opaque`** (défaut) : structure libre, clé/valeur quelconques.
- **`kubernetes.io/tls`** : attend exactement les clés `tls.crt` et
  `tls.key` — c'est le format qu'un Ingress consomme pour servir du
  HTTPS. Exemple de forme (non appliqué) dans
  `k8s/secret-tls-example.yaml`.
- **`kubernetes.io/dockerconfigjson`** : credentials pour tirer une
  image depuis un registry Docker privé (`imagePullSecrets` sur un
  Pod).
- **`kubernetes.io/basic-auth`** / **`kubernetes.io/ssh-auth`** :
  structures prédéfinies pour des identifiants basic-auth ou une clé SSH.
- **`kubernetes.io/service-account-token`** : créé automatiquement par
  Kubernetes pour authentifier un Pod auprès de l'API server.

## Ce qu'on va en faire ensuite

À l'étape suivante, on ajoute une vraie base de données — et son mot de
passe sera, sans surprise, stocké dans un Secret plutôt qu'une
ConfigMap.

## Étape suivante

```bash
git checkout step-8-database-pv
cat STEP.md
```
