# TP 0 — Recette du laboratoire Kubernetes (édition formateur)

> **Toutes les commandes de TP0 (Linux/WSL2, PowerShell, macOS) sont regroupées dans [TP0-commandes.md](TP0-commandes.md)**. Le présent document détaille les raisons, les limites et le dépannage.

**Périmètre :** Minikube v1.39+ sur trois nœuds (un control-plane, deux workers), Docker comme driver, `containerd` comme runtime, Calico comme CNI, Traefik, storage-provisioner/default-storageclass, CSI Hostpath et ingress-dns (selon accessibilité réseau du poste).

L'installation est **réalisée par les étudiants**, pas automatiquement par une commande opaque. Ce guide constitue une recette et une aide au diagnostic, en complément du [livret INFAL127](https://docs.google.com/document/d/1tULJJfFAIKUSN0MpHH2MQZ1VNsENxxCd6jCnYflQD1M/edit). Les commandes ci-dessous sont des exemples à comprendre, pas un corrigé des TP applicatifs.

## 1. Préflight hôte

Vérifier les outils `docker version`, `docker info`, `minikube version`, `kubectl version --client` et `python3 --version` (Python 3.10+ pour notre validateur). Installer Minikube au minimum en **v1.39.0** pour l'addon Traefik.

Installations officielles :
- [Docker](https://docs.docker.com/get-started/get-docker/)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl Linux](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/), [Windows](https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/), [macOS](https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/)
- [K9s, facultatif](https://github.com/derailed/k9s#installation)

**Dimensionnement :** `--cpus=2 --memory=2560` dans l'exemple affecte ces ressources **par nœud**. Pour trois nœuds, prévoir approximativement 6 vCPU virtuels et 7,5 Gio de mémoire invitée, plus le système hôte et Docker. Ces valeurs sont un point de départ à tester ; sur les postes avec RAM limitée, adapter. Le délai TP 0 de 60 minutes est un objectif nominal, pas une garantie.

## 2. Créer le cluster (Linux/macOS, bash)

```bash
minikube start -p opsboard-lab \
  --driver=docker --nodes=3 --cni=calico \
  --container-runtime=containerd \
  --cpus=2 --memory=2560

kubectl config use-context opsboard-lab
kubectl get nodes -o wide
kubectl get pods -A
```

Sur **PowerShell**, saisir la commande `minikube start` en une seule ligne (ou utiliser le backtick PowerShell plutôt que les barres obliques inverses bash) :

```powershell
minikube start -p opsboard-lab --driver=docker --nodes=3 --cni=calico --container-runtime=containerd --cpus=2 --memory=2560
kubectl config use-context opsboard-lab
kubectl get nodes -o wide
kubectl get pods -A
```

**Ne jamais changer de contexte au hasard** : inspecter `kubectl config current-context` avant toute opération destructive.

## 3. Addons minimaux

```bash
# Vérifier en premier les addons fournis par défaut
minikube addons list -p opsboard-lab

# Si absents / disabled, activer les deux addons standard
minikube addons enable storage-provisioner -p opsboard-lab
minikube addons enable default-storageclass -p opsboard-lab

# CSI Hostpath : provisionnement multinœud (stockage local, NON répliqué)
minikube addons enable csi-hostpath-driver -p opsboard-lab

# Choisir Traefik, NE PAS activer l'ancien addon "ingress" (ingress-nginx)
minikube addons enable traefik -p opsboard-lab

# DNS local des Ingress : activer seulement si nécessaire,
# puis vérifier la résolution ET le chemin réseau du système hôte.
minikube addons enable ingress-dns -p opsboard-lab

kubectl get storageclass
kubectl get csidrivers
kubectl get ingressclass
kubectl get pods -A
kubectl get service -n kube-system traefik
kubectl create namespace opsboard
```

La StorageClass `standard` n'assure **pas** la mobilité de volumes sur tous les nœuds. Pour les exercices avec PVC, utiliser explicitement `storageClassName: csi-hostpath-sc`. Le pilote CSI Hostpath crée des volumes locaux au nœud : il ne fournit ni réplication, ni sauvegarde, ni haute disponibilité inter-nœuds.

**Ingress :** Minikube 1.39+ propose l'addon `traefik` basé sur Helm. Les addons `ingress` (nginx) et `traefik` ne peuvent pas être activés ensemble : conflit de ports 80/443. Un Ingress applicatif sera créé au TP 8, pas dans le TP 0.

**Ingress DNS :** le guide historique Minikube décrit l'addon avec `ingress` (nginx) ; nous évitons ce contrôleur retiré. Nous devons **valider le comportement ingress-dns + Traefik** avant de modifier la configuration DNS de tout un poste. L'activation seule ne modifie pas automatiquement le résolveur hôte, et il est déconseillé de changer `/etc/resolv.conf` globalement sans méthode de retour arrière. Le test HTTP(S) et DNS effectif relève du TP 8.

## 4. Vérifier les prérequis avec notre script de lecture seule

```bash
python3 scripts/lab/verify.py --profile opsboard-lab
# Si ingress-dns a été activé et que vous voulez le rendre bloquant :
python3 scripts/lab/verify.py --profile opsboard-lab --require-ingress-dns
```

Le validateur examine les nœuds Ready, le contexte, le runtime, Calico (DaemonSet réparti sur les trois nœuds), CoreDNS, Traefik, IngressClass, StorageClasses, driver CSI et namespace. Il ne modifie rien et n'est **pas** un corrigé pour créer les ressources.

## 5. Vérifications réseau supplémentaires (TP 8 et dry-run)

| Environnement hôte | Accès à Minikube | DNS / Ingress |
| --- | --- | --- |
| Linux + Docker | IP Minikube souvent directement joignable ; vérifier `minikube ip -p opsboard-lab` | `ingress-dns` peut répondre à la requête DNS, mais le résolveur hôte doit être configuré **par suffixe `.test`**, puis réellement testé |
| Windows + Docker Desktop | L'IP du nœud peut ne pas être accessible directement depuis l'hôte | Ne pas créer de règle DNS permanente vers une IP injoignable ; utiliser l'exposition adaptée, `minikube service --url` ou un port-forward selon le cas |
| macOS + Docker Desktop | Même restriction possible pour l'IP du nœud | Vérifier route et DNS séparément ; ne pas supposer que la configuration `/etc/resolver` suffit si l'IP n'est pas joignable |
| WSL2 | Le réseau Docker/WSL et l'hôte Windows ne partagent pas nécessairement les mêmes chemins | Tester `curl` depuis WSL **et** le navigateur Windows ; documenter la différence |

Aucun changement DNS permanent ne doit être appliqué automatiquement par la recette. Choisir le suffixe `.test` (pas `.localhost` ni `.local`).

Test de principe **après** création d'un Ingress `opsboard.test` :

```bash
# Linux avec IP directement accessible
IP="$(minikube ip -p opsboard-lab)"
curl --max-time 5 -H 'Host: opsboard.test' "http://$IP/"
# Tester séparément le DNS : nslookup opsboard.test "$IP"
```

Le DNS, l'exposition HTTP et la NetworkPolicy sont **trois sujets indépendants** à tester séparément.

## 6. Stop, reprise et dépannage

```bash
minikube stop -p opsboard-lab
minikube start -p opsboard-lab
kubectl get nodes
python3 scripts/lab/verify.py
```

Si un nœud est `NotReady`, consulter d'abord `kubectl get events -A --sort-by=.lastTimestamp`, l'état de Calico et les ressources CPU/mémoire, avant de supprimer le profil. Si Traefik est absent : `kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik`. Si un PVC est `Pending` : `kubectl describe pvc ...`, vérifier sa StorageClass et le nœud cible.

Le test de CI sur GitHub Actions vérifie **Linux uniquement**. Il ne prouve pas l'installation sur un poste CESI Windows/macOS, ni le respect effectif du temps nominal de 60 minutes. Ces points restent à mesurer lors du dry-run.

## Références Minikube

- [Traefik addon](https://minikube.sigs.k8s.io/docs/handbook/addons/traefik/)
- [Multi-node](https://minikube.sigs.k8s.io/docs/tutorials/multi_node/)
- [CSI Hostpath](https://minikube.sigs.k8s.io/docs/tutorials/volume_snapshots_and_csi/)
- [Ingress DNS](https://minikube.sigs.k8s.io/docs/handbook/addons/ingress-dns/)
- [Docker driver](https://minikube.sigs.k8s.io/docs/drivers/docker/)
