# TP 5 — Images pédagogiques pour rolling update et rollback

Les images du TP 5 sont construites à partir du **même code source** et présentent des versions d'exécution différentes, figées lors de la construction. Elles permettent d'observer un vrai changement de révision de Deployment et un incident de mise à jour, sans modifier le frontend ni construire de code en classe.

| Image API | Utilisation dans le cours |
| --- | --- |
| `ghcr.io/sebastien-ribiere/opsboard-api:tp5-v1` | Release de départ |
| `ghcr.io/sebastien-ribiere/opsboard-api:tp5-v2` | Nouvelle release à déployer |
| `ghcr.io/sebastien-ribiere/opsboard-api:tp5-incident` | Release d'incident à diagnostiquer puis à restaurer |

> Ces tags de confort sont **mutables** ; le pipeline publie également des tags `tp5-<variante>-<sha-Git-complet>`. Pour un TP strictement reproductible, utilisez le tag lié au commit ou, de préférence, le digest SHA-256 publié. N'utilisez pas `latest`.

La publication est pilotée par [teaching-releases.yml](../.github/workflows/teaching-releases.yml), uniquement depuis `main`. Les pull requests reconstruisent et testent les trois variantes, y compris l'incident attendu, et les passent au scan Trivy. Sur `main`, chaque image est publiée avec SBOM, provenance BuildKit et signature Cosign.

## Critères d'observation pour le TP 5

1. Après déploiement de la release initiale, `/version` permet de constater sa version.
2. Un changement d'image amène Kubernetes à créer un nouveau ReplicaSet ; les Pods sont progressivement remplacés.
3. Les sondes `readiness` influencent la disponibilité réelle lors de la mise à jour. Réglez une stratégie de rolling update et des seuils adaptés.
4. Une release problématique doit être investiguée avant l'exécution d'un rollback.
5. La correction ou le rollback doit laisser les manifests et la version finale cohérents.

**Le livret reste l'énoncé officiel.** Cette page est un inventaire des artefacts, pas une solution du TP. Les scénarios d'injection plus avancés et les corrigés enseignants ne seront pas publiés ici.

- [Énoncés OpsBoard (TP 0–12)](https://docs.google.com/document/d/1tULJJfFAIKUSN0MpHH2MQZ1VNsENxxCd6jCnYflQD1M/edit)
- [Présentation INFAL127](https://docs.google.com/presentation/d/1pw9Hh1V6d0zZviU7YH1aCVVHZDYhyV0HV8fsSzmIM6U/edit)

## Prérequis à valider avant le cours

- Publication du workflow et accès anonyme aux trois images.
- Validation des signatures Cosign et consignation des digests exacts des variantes.
- Un cluster Minikube fonctionnel avec l'API et le frontend OpsBoard.
- Un Deployment API comportant une `readinessProbe` fonctionnelle ; sans cette sonde, une panne de disponibilité peut rester invisible lors d'une rolling update.
- Une stratégie de déploiement préservant les réplicas sains pendant une mise à jour ; tester les propriétés `maxSurge` et `maxUnavailable`.
