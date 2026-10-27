# Étape 0 — Juste une image Docker

Avant de parler de Kubernetes, on part de la brique de base : une image
Docker qui fait tourner un serveur web `nginx` servant une page statique.
Pas de cluster, pas de `kubectl` ici — l'idée est d'avoir un point de
départ bien compris avant d'empiler les couches Kubernetes par-dessus.

## Ce qu'il y a dans ce dossier

- `app/Dockerfile` — construit une image à partir de `nginx:1.27-alpine`
  et y copie notre page `index.html`.
- `app/index.html` — la page affichée.

## Essayer

Construire l'image :

```bash
docker build -t k8s-tutorial-web:step0 app/
```

La lancer :

```bash
docker run --rm -p 8080:80 k8s-tutorial-web:step0
```

Puis ouvrir http://localhost:8080 — tu dois voir la page "Étape 0 : Docker".

Arrêter avec `Ctrl+C`.

## Pourquoi c'est important pour la suite

Kubernetes ne sait pas "construire" une appli : il sait seulement
**faire tourner des conteneurs à partir d'images**, et gérer leur cycle
de vie (redémarrage, réplication, mise à jour, exposition réseau...).
Tout ce qu'on va ajouter dans les prochaines étapes orbite autour de
cette unique image Docker — on ne va jamais la changer tant qu'on ne
parlera pas de ConfigMap/Secret/base de données.

À noter : ici, si le conteneur plante, rien ne le relance. Si on veut
plusieurs instances, il faut lancer plusieurs `docker run` à la main et
gérer soi-même la répartition du trafic. C'est exactement le problème
que Kubernetes résout, à partir de l'étape suivante.

## Étape suivante

```bash
git checkout step-1-pod
cat STEP.md
```

On y introduit le **Pod**, la plus petite unité déployable de Kubernetes.
