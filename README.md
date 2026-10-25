# OpsBoard — Kubernetes Lab

[![CI & Supply Chain](https://github.com/sebastien-ribiere/OpsBoard/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastien-ribiere/OpsBoard/actions/workflows/ci.yml)

**Projet compagnon du module CESI INFAL127 — Plateforme d'orchestration des clusters applicatifs.**

OpsBoard est une petite application distribuée intentionnellement simple. Ce dépôt fournit le code et les images qui servent aux exercices Kubernetes du fil rouge. Les étudiants construisent eux-mêmes leur cluster Minikube, avec **trois nœuds, Calico et les addons utiles**, puis déploient et exploitent OpsBoard.

> Ce projet est un support pédagogique, **pas** une plateforme de production.

## Supports du cours

| Ressource | Lien |
| --- | --- |
| **Livret des TP (TP 0 à TP 12)** | [Lire le livret Google Docs](https://docs.google.com/document/d/1tULJJfFAIKUSN0MpHH2MQZ1VNsENxxCd6jCnYflQD1M/edit) |
| **Diaporama du cours** | [Ouvrir INFAL127 sur Google Slides](https://docs.google.com/presentation/d/1pw9Hh1V6d0zZviU7YH1aCVVHZDYhyV0HV8fsSzmIM6U/edit) |
| **Chaîne CI / publication** | [GitHub Actions](https://github.com/sebastien-ribiere/OpsBoard/actions/workflows/ci.yml) |

Le **livret de TP est la source des consignes et des validations**. Ce README explique seulement comment démarrer l'application et comment sont construites ses images.

## Architecture

```text
Navigateur
   |
   v
opsboard-web (NGINX non-root, port 8080)
   |  GET /api/*  [proxy vers le Service interne]
   v
opsboard-api (Python standard library, port 8080)
   |--- /status
   |--- /version
   |--- /health/live
   |--- /health/ready
   '--- /health/startup
```

Dans Kubernetes, créez un **Service ClusterIP nommé `opsboard-api`** pour l'API, et un Service dédié au frontend. Le proxy NGINX utilise ce nom DNS. Le DNS du navigateur ne résout jamais directement le nom du Service interne.

Aucune base de données n'est nécessaire pour les TP obligatoires. Le stockage PVC constitue une extension possible.

## Démarrage rapide (pour valider l'application)

**Prérequis :** Docker avec le plugin Compose v2.

```bash
git clone https://github.com/sebastien-ribiere/OpsBoard.git
cd OpsBoard
docker compose up --build -d

# Tester la page web et les endpoints via NGINX
curl -fsS http://localhost:8080/healthz
curl -fsS http://localhost:8080/api/status
curl -fsS http://localhost:8080/api/version

# Nettoyer
docker compose down
```

Ouvrez ensuite [http://localhost:8080](http://localhost:8080).

**Important :** Compose sert ici à vérifier les images. Pendant les exercices, les étudiants déploient Kubernetes en YAML et créent eux-mêmes les ressources demandées ; n'utilisez pas Compose comme solution de substitution au fil rouge.

## Construire les images

```bash
docker build -f api/Dockerfile -t opsboard-api:local .
docker build -f web/Dockerfile -t opsboard-web:local .

# Tests sans dépendances Python tierces
python -m unittest discover -s tests -v
```

Après fusion sur `main`, la CI est conçue pour publier automatiquement les images dans **GitHub Container Registry** :

- `ghcr.io/sebastien-ribiere/opsboard-api:latest`
- `ghcr.io/sebastien-ribiere/opsboard-web:latest`
- Tags immuables au niveau Git SHA : `sha-<commit-complet>`
- Tags de version lorsque l'on pousse un tag Git `vX.Y.Z`

### Images publiques validées (publication du 25 octobre 2026)

Les deux images ci-dessous ont été **téléchargées anonymement et vérifiées avec Cosign** depuis un runner GitHub sans accès privilégié à GHCR. Pour les TP, privilégiez ces digests plutôt que `latest`, qui peut évoluer :

```bash
docker pull ghcr.io/sebastien-ribiere/opsboard-api@sha256:38adf270e324f8c955abac09fd3cbdd336925078f74890fc35df22ef295bc0b1
docker pull ghcr.io/sebastien-ribiere/opsboard-web@sha256:b885b991b1d80064fdbd9ac55658ee1c06eb78a44ffe94baab109e4b1016cb40
```

Le tag de commit correspondant est `sha-6aa20529e64dab81ade8a4af3ba54a12bc1e2a17` pour les deux images. Contrairement aux digests, les tags ne sont pas intrinsèquement immuables.

Pour vérifier la signature keyless (si `cosign` est installé) :

```bash
cosign verify \
  --certificate-identity 'https://github.com/sebastien-ribiere/OpsBoard/.github/workflows/ci.yml@refs/heads/main' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  ghcr.io/sebastien-ribiere/opsboard-api@sha256:38adf270e324f8c955abac09fd3cbdd336925078f74890fc35df22ef295bc0b1
```

Même commande pour `opsboard-web` en remplaçant son nom et son digest. Le [test automatisé de tirage anonyme et de signature](.github/workflows/verify-ghcr-public.yml) valide les deux images sans authentification, et échoue si elles ne sont plus accessibles ou si la signature attendue manque.

## Simuler les incidents de santé

La configuration de l'API se fait par variables d'environnement au démarrage du conteneur :

| Variable | Défaut | Usage dans les TP |
| --- | --- | --- |
| `ENVIRONNEMENT` | `lab` | ConfigMap / environnement |
| `MESSAGE_BANNIERE` | `Kubernetes est prêt !` | ConfigMap / redémarrage |
| `APP_VERSION` | `dev` | Contrôle de version |
| `OPSBOARD_READY` | `true` | `false` : readiness HTTP 503 |
| `OPSBOARD_LIVE` | `true` | `false` : liveness HTTP 503 |
| `STARTUP_DELAY_SECONDS` | `0` | Délai simulé avant le succès de startup |
| `SVC_TOKEN` | absent | Valeur fictive pour le TP Secret, jamais retournée par l'API |

Par exemple, pour le TP probes, faites évoluer les variables dans le Deployment et observez les événements, les EndpointSlices et les redémarrages. **Ne déployez pas le mode de panne volontaire en production.**

Le endpoint de version retourne `APP_VERSION`. La CI le renseigne au build par SHA Git ; les exercices peuvent aussi utiliser des images taguées v1/v2 lors de la préparation des scénarios.

## Parcours pédagogique

Les 13 TP suivent : installation du cluster → Pod → Deployments et Services → ConfigMaps → probes → rolling update / rollback → diagnostic → Secrets → Ingress TLS → cert-manager → Helm → RBAC/NetworkPolicy → incident final.

Ce dépôt fournit **l'application de base et sa CI**. Les manifests étudiants, les Chart Helm, les jeux d'incident de l'enseignant et les corrigés seront ajoutés progressivement. Leur absence dans cette première PR est volontaire : ils constituent le travail des TP ou du matériel de préparation, pas des solutions à livrer aux étudiants.

## Chaîne CI/CD et sécurité

[Voir le workflow](.github/workflows/ci.yml). Lors d'une pull request :

1. Lint Python (Ruff), contrôles SAST (Bandit), tests unitaires et syntaxe JS.
2. Recherche de secrets (Gitleaks) et analyse du dépôt (Trivy).
3. Test d'intégration du frontend et de l'API avec Docker Compose.
4. Construction **des deux images**, scan de vulnérabilités HIGH/CRITICAL (Trivy). Un échec bloque la publication.

Sur `main` ou un tag `v*`, **seulement après réussite des contrôles**, le pipeline est conçu pour publier dans GHCR avec un jeton GitHub à permissions limitées, une SBOM et une attestation de provenance BuildKit, puis signer chaque image **par digest avec Cosign et OIDC** (sans clé privée longue durée).

L'image API utilise un runtime Python **distroless sans shell** ; pour l'inspection d'un Pod, utiliser les logs, les sondes, les événements et éventuellement un conteneur de debug éphémère.

Les permissions `packages: write` et `id-token: write` ne sont accordées qu'au job de publication. Les dépendances Actions et Docker sont surveillées par Dependabot. Les actions sont référencées par SHA de commit.

**Limites :** les tags des images de base restent flottants pour recevoir les mises à jour de sécurité ; un scan peut bloquer une livraison si l'amont publie une vulnérabilité. Les images ne sont pas encore déployées automatiquement sur un cluster. Ni l'existence d'une SBOM, ni un scan réussi, ni une signature ne garantissent l'absence de vulnérabilités.

## Aide au diagnostic

- Le frontend est visible mais l'API ne répond pas : vérifier le Service `opsboard-api`, ses EndpointSlices, les Pods et la résolution DNS interne.
- Un Pod est `Running` mais pas `Ready` : vérifier `/health/ready` et les probes.
- Une connexion Ingress échoue : vérifier Traefik, l'IngressClass, le nom d'hôte et le chemin TLS.
- Le scan Trivy bloque : mettre à jour l'image de base et analyser les CVE ; ne pas désactiver le gate sans justification.
- Docker sous Windows/macOS : les méthodes d'accès à Minikube diffèrent ; suivre les indications du [TP 0](https://docs.google.com/document/d/1tULJJfFAIKUSN0MpHH2MQZ1VNsENxxCd6jCnYflQD1M/edit).

## Licence et sécurité

Consultez [LICENSE](LICENSE) et [SECURITY.md](SECURITY.md). N'ajoutez jamais de véritables Secrets Kubernetes, de clés privées TLS, de jetons GitHub ou d'identifiants personnels aux exemples.
