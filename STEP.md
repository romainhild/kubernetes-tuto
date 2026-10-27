# Étape 6 — Le ConfigMap

Jusqu'ici, la seule façon de changer le contenu de la page était de
reconstruire l'image Docker. Un **ConfigMap** permet d'injecter de la
configuration (ou même des fichiers entiers) dans un Pod *sans toucher à
l'image* — pratique pour changer un comportement entre dev/staging/prod,
ou pour itérer sans rebuild.

## Nouveau fichier

- `k8s/configmap.yaml` — contient deux clés :
  - `WELCOME_MESSAGE` : une simple valeur texte,
  - `index.html` : un fichier HTML complet (une ConfigMap peut stocker
    n'importe quel fichier texte, pas seulement des paires clé/valeur
    courtes — limite : 1 MiB au total par ConfigMap).

Et `k8s/deployment.yaml` a été modifié pour la consommer, **des deux
façons possibles** :

### 1. Comme variable d'environnement

```yaml
env:
  - name: WELCOME_MESSAGE
    valueFrom:
      configMapKeyRef:
        name: web-content
        key: WELCOME_MESSAGE
```

(Il existe aussi `envFrom: configMapRef:` pour injecter *toutes* les
clés d'un coup comme variables d'env — on ne l'utilise pas ici parce que
la clé `index.html` n'est pas un nom de variable d'environnement valide.)

### 2. Comme fichier monté (volume)

```yaml
volumeMounts:
  - name: web-content
    mountPath: /usr/share/nginx/html/index.html
    subPath: index.html
volumes:
  - name: web-content
    configMap:
      name: web-content
```

Le `subPath` permet de monter **une seule clé** de la ConfigMap sur un
fichier précis, sans écraser tout le dossier `/usr/share/nginx/html/`
(sans `subPath`, le volume remplacerait tout le contenu du dossier par
les clés de la ConfigMap).

## Essayer

```bash
kubectl apply -f k8s/configmap.yaml -f k8s/deployment.yaml
kubectl rollout status deployment/web -n tutorial-app
kubectl port-forward -n tutorial-app service/web 8080:80
```

Ouvre http://localhost:8080 : la page vient maintenant de la ConfigMap,
alors que l'image Docker utilisée est **exactement la même** qu'à
l'étape 0.

Vérifie la variable d'environnement :

```bash
kubectl exec -n tutorial-app deploy/web -- env | grep WELCOME_MESSAGE
```

## Démonstration : mettre à jour sans toucher à l'image

```bash
kubectl edit configmap web-content -n tutorial-app
# change le texte de index.html, sauvegarde
```

En général, un fichier monté en volume depuis une ConfigMap se met à
jour **tout seul** après quelques secondes à quelques minutes (le
kubelet resynchronise périodiquement), sans redémarrer le Pod.

⚠️ **Mais pas ici.** Dès qu'on utilise `subPath` (notre cas, pour ne
monter que la clé `index.html` sans écraser tout le dossier), ce
mécanisme de mise à jour automatique est **désactivé** — c'est une
limitation documentée de Kubernetes, pas une question de délai : un
fichier monté via `subPath` ne reçoit jamais les mises à jour de la
ConfigMap tant que le Pod n'est pas recréé. Rafraîchir la page ne
suffira donc pas, même en attendant.

Pour voir le changement, il faut forcer un nouveau rollout :

```bash
kubectl rollout restart deployment/web -n tutorial-app
kubectl rollout status deployment/web -n tutorial-app
```

La variable d'environnement `WELCOME_MESSAGE`, elle, ne se mettra pas
à jour non plus dans les Pods déjà démarrés — les variables d'env sont
de toute façon toujours figées au démarrage du conteneur, `subPath` ou
pas. Le même `rollout restart` ci-dessus la reprendra aussi.

**À retenir :** un volume de ConfigMap *sans* `subPath` se mettrait à
jour en live ; dès que tu ajoutes un `subPath` (souvent nécessaire pour
ne monter qu'un seul fichier sans écraser tout un dossier), tu perds
cette mise à jour automatique et tu dois forcer un rollout. C'est un
vrai piège rencontré fréquemment en pratique (par exemple pour monter
un seul fichier de config dans un dossier qui contient aussi des
binaires de l'image).

## Autres détails utiles

- `kubectl create configmap mon-config --from-file=chemin/fichier.conf`
  permet de créer une ConfigMap directement depuis un fichier, sans
  écrire le YAML à la main.
- Une ConfigMap peut être marquée `immutable: true` : Kubernetes refuse
  alors toute modification (il faut en créer une nouvelle avec un autre
  nom). Ça évite des mises à jour accidentelles, et accélère un peu les
  performances du cluster sur de gros clusters.
- Une ConfigMap **n'est pas chiffrée** et est lisible par quiconque a le
  droit de lire les ConfigMaps du namespace. Pour une information
  sensible (mot de passe, token, clé API), il faut un **Secret** — c'est
  l'étape suivante.

## Étape suivante

```bash
git checkout step-7-secret
cat STEP.md
```
