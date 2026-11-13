# TP 0 — Manifestes YAML de validation

Ces trois fichiers valident les namespaces et le montage d'un PVC avec le CSI Hostpath Minikube. Les installations de Minikube, de Calico, de Traefik et d'ingress-dns se font via les commandes `minikube start` et `minikube addons enable` du [runbook TP0](../../teaching/TP0-commandes.md). Aucun fichier YAML supplémentaire n'est nécessaire pour activer ces addons.

## Appliquer, dans cet ordre

```bash
kubectl config current-context # doit afficher opsboard-lab
kubectl apply -f 00-namespaces.yaml
kubectl apply -f 10-csi-pvc.yaml
kubectl apply -f 20-csi-pod.yaml

kubectl wait -n tp0-smoke --for=condition=Ready pod/volume-consumer --timeout=240s
kubectl get pvc,pod -n tp0-smoke -o wide
kubectl describe pvc data -n tp0-smoke
```

Attendus : PVC `data` en `Bound` et Pod `volume-consumer` en `Running` avec condition `Ready`. Cette recette confirme le **provisionnement et le montage** du volume ; elle ne prouve ni la persistance après déplacement de nœud ni une haute disponibilité du stockage.

Test HTTP facultatif via `kubectl port-forward -n tp0-smoke pod/volume-consumer 18080:8080` dans un premier terminal, puis `curl http://localhost:18080/health/ready` depuis un second terminal.

## Nettoyer uniquement le test CSI

```bash
kubectl delete namespace tp0-smoke
```

Le namespace `opsboard` reste disponible pour les TP 1 à 12. Le manifeste du Pod utilise un **digest d'image versionné** déjà validé publiquement. Si la publication évolue, vérifier l'accessibilité de ce digest.
