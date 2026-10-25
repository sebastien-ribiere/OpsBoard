# TP 4 — Probes manipulables en cours d'exécution

Ce guide complète le [livret officiel des TP](https://docs.google.com/document/d/1tULJJfFAIKUSN0MpHH2MQZ1VNsENxxCd6jCnYflQD1M/edit). Il décrit **comment injecter des pannes contrôlées**, sans fournir les manifests Kubernetes corrigés.

## Objectifs vérifiables

| Test | Commande de déclenchement | Comportement attendu |
| --- | --- | --- |
| Readiness | `SIGUSR1` | HTTP 503 sur `/health/ready` ; le Pod reste Running et son endpoint n'est plus Ready |
| Liveness | `SIGUSR2` | HTTP 503 sur `/health/live` ; le kubelet redémarre le conteneur **si** une livenessProbe adaptée est configurée |
| Startup | `STARTUP_DELAY_SECONDS` | HTTP 503 sur `/health/startup` pendant le démarrage, puis HTTP 200 lorsque le délai est écoulé |

## Activer le mode laboratoire

L'application **n'accepte aucun signal pédagogique par défaut**. Configurez explicitement `OPSBOARD_ENABLE_LAB_SIGNALS=true` dans l'environnement du Deployment API de votre laboratoire. Appliquez votre configuration Kubernetes et attendez le nouveau Pod Ready.

L'image de l'API est *distroless* et ne contient **aucun shell**. En revanche, elle contient l'interpréteur `/usr/bin/python3`, utilisable pour envoyer un signal au processus principal (PID 1).

Sélectionnez le Pod API à tester et remplacez `NOM_DU_POD` dans les commandes suivantes. Pour plusieurs replicas, un signal ne concerne **qu'un seul Pod**, et non l'ensemble du Deployment.

### Faire basculer la readiness

```bash
kubectl exec -n opsboard NOM_DU_POD -- /usr/bin/python3 -c 'import os,signal; os.kill(1,signal.SIGUSR1)'
```

- Observez l'état Ready du Pod et les endpoints du Service.
- La readiness probe échouée **ne redémarre pas le conteneur** par elle-même.
- Relancez la même commande pour restaurer la readiness, puis contrôlez son retour.

### Faire basculer la liveness

```bash
kubectl exec -n opsboard NOM_DU_POD -- /usr/bin/python3 -c 'import os,signal; os.kill(1,signal.SIGUSR2)'
```

- Relevez `kubectl get pods -n opsboard -w`, les événements et le compteur `RESTARTS`.
- Le redémarrage dépend des paramètres de votre `livenessProbe` : `periodSeconds`, `timeoutSeconds` et `failureThreshold`.
- Au redémarrage du **conteneur**, l'état des signaux revient aux valeurs initiales.

### Démontrer la startup probe

Dans les variables de configuration de l'API, définissez un délai de laboratoire, par exemple `STARTUP_DELAY_SECONDS=20`. Redéployez, puis observez `/health/startup` et le comportement de vos probes. Une startup probe configurée correctement empêche que la liveness ne pénalise le démarrage initial.

## Consignes de sécurité et limites

- Utilisez uniquement un **cluster local de formation**, avec un namespace dédié. N'activez jamais `OPSBOARD_ENABLE_LAB_SIGNALS` dans une version de production.
- Aucune route HTTP d'administration ne permet d'activer ou désactiver les pannes : les opérations passent par l'autorisation Kubernetes `pods/exec`.
- L'action est **volontairement éphémère** : la suppression/recréation du conteneur efface son état mémoire.
- Une panne de liveness peut rendre les commandes `exec` impossibles jusqu'à la recréation du conteneur ; c'est un comportement attendu.
- Ne confondez pas "processus Running", "Pod Ready", présence dans les EndpointSlices et disponibilité du Service.
- Les noms de Pod et labels dépendent des manifests créés par les étudiants. Ne copiez pas de ressources Kubernetes d'un autre exercice.

## Validation minimale

1. Readiness passe de 200 à 503, **sans redémarrage** du conteneur. Un nouvel appel au signal rétablit 200.
2. Liveness passe à 503, et un redémarrage est observable si la livenessProbe est présente.
3. Le délai de startup est mesurable et n'empêche pas le démarrage normal après expiration.

L'épreuve de bout en bout de ces trois comportements dans **Minikube à trois nœuds** est prévue lors du dry-run Jour 1 de la [roadmap #5](https://github.com/sebastien-ribiere/OpsBoard/issues/5).
