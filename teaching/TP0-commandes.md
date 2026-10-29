# TP 0 — Toutes les commandes, au même endroit

**Version consolidée pour les étudiants · Linux/WSL2, Windows PowerShell et macOS.**

Objectif : cluster `opsboard-lab` à **3 nœuds** avec `containerd`, Calico, CoreDNS, Traefik, CSI Hostpath et namespace `opsboard`. Basé sur la [recette Linux réussie](https://github.com/sebastien-ribiere/OpsBoard/actions/runs/40231413805). Le livret officiel est [ici](https://docs.google.com/document/d/1tULJJfFAIKUSN0MpHH2MQZ1VNsENxxCd6jCnYflQD1M/edit).

> **Pré-requis** : Docker Engine ou Docker Desktop **déjà démarré** en mode conteneurs Linux. Si Docker n'est pas installé, suivre [Docker](https://docs.docker.com/get-started/get-docker/). Sous Windows, activer au besoin l'intégration WSL2 dans Docker Desktop. Ne pas exécuter les commandes d'installation Linux dans PowerShell ni les commandes PowerShell dans Bash.

## A — Installer les outils (choisir son OS)

### Linux / Ubuntu / WSL2 x86-64 (Bash)

Si Minikube et kubectl sont déjà installés dans des versions compatibles, sauter leur installation.

```bash
# Minikube 1.39.0 — version utilisée pour notre recette
curl -fL -o /tmp/minikube https://github.com/kubernetes/minikube/releases/download/v1.39.0/minikube-linux-amd64
sudo install -m 0755 /tmp/minikube /usr/local/bin/minikube

# kubectl v1.37.0 — aligné avec le serveur de la recette
curl -fL -o /tmp/kubectl https://dl.k8s.io/release/v1.37.0/bin/linux/amd64/kubectl
sudo install -m 0755 /tmp/kubectl /usr/local/bin/kubectl

# Optionnel : K9s sur Ubuntu x86-64
# wget -q https://github.com/derailed/k9s/releases/latest/download/k9s_linux_amd64.deb
# sudo apt install ./k9s_linux_amd64.deb
```

Pour Linux ARM64, consulter les [binaires Minikube](https://minikube.sigs.k8s.io/docs/start/) et les [binaires kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/) propres à cette architecture.

### Windows (PowerShell)

```powershell
winget install -e --id Kubernetes.minikube
winget install -e --id Kubernetes.kubectl

# Optionnel : console K9s
# winget install k9s
```

Fermer puis rouvrir PowerShell si les exécutables ne sont pas trouvés. Les installations Winget utilisent la dernière version disponible : vérifiez la compatibilité Minikube 1.39+ et kubectl dans ±1 version mineure du serveur.

### macOS (Terminal)

```bash
brew install minikube kubectl
# Optionnel :
# brew install derailed/k9s/k9s
```

## B — Création, addons et contrôle (commandes communes à Bash et PowerShell)

**Exécuter ces commandes dans l'ordre**, dans le terminal où Docker, Minikube et kubectl sont accessibles. La commande `minikube start` est écrite sur **une seule ligne**, pour fonctionner sous Bash et PowerShell.

```sh
# 1. Contrôler les outils et le moteur Docker
docker version
docker info
minikube version
kubectl version --client

# 2. Créer un cluster 3 nœuds avec Calico / containerd
minikube start -p opsboard-lab --driver=docker --nodes=3 --cni=calico --container-runtime=containerd --kubernetes-version=v1.37.0 --cpus=2 --memory=2560

# 3. Protéger le contexte et attendre les 3 nœuds
kubectl config current-context
kubectl config use-context opsboard-lab
kubectl wait --for=condition=Ready nodes --all --timeout=360s
kubectl get nodes -o wide

# 4. Inventorier et activer les addons du TP 0
minikube addons list -p opsboard-lab
minikube addons enable storage-provisioner -p opsboard-lab
minikube addons enable default-storageclass -p opsboard-lab
minikube addons enable csi-hostpath-driver -p opsboard-lab
minikube addons enable traefik -p opsboard-lab
minikube addons enable ingress-dns -p opsboard-lab

# 5. Namespace du fil rouge (commande idempotente)
kubectl create namespace opsboard --dry-run=client -o yaml | kubectl apply -f -

# 6. Vérifier réseau, stockage, ingress et workloads
minikube status -p opsboard-lab
kubectl get pods -A -o wide
kubectl get storageclass
kubectl get csidrivers
kubectl get ingressclass
kubectl get svc -n kube-system traefik
kubectl get namespace opsboard
minikube addons list -p opsboard-lab
```

**Attention :** l'activation de `ingress-dns` installe le service dans le cluster ; elle **ne configure pas le DNS du poste**. Cela sera testé au TP Ingress. Sous Windows/macOS et Docker Desktop, `minikube ip` n'est pas forcément directement accessible depuis l'hôte. Le CSI Hostpath **ne réplique pas** les données entre nœuds. Ne pas activer l'ancien addon `ingress` (NGINX), incompatible avec Traefik.

## C — Vérification automatique, facultative

Ces commandes nécessitent Git et Python 3.10+. Le fichier `scripts/lab/verify.py` appartient à la [PR de recette TP0](https://github.com/sebastien-ribiere/OpsBoard/pull/11) jusqu'à sa fusion.

```bash
git clone https://github.com/sebastien-ribiere/OpsBoard.git
cd OpsBoard
# Tant que la PR #11 n'est pas fusionnée :
git fetch origin feat/tp0-minikube-lab-recipe
git switch --track origin/feat/tp0-minikube-lab-recipe
# Sur Linux/WSL2/macOS :
python3 scripts/lab/verify.py --profile opsboard-lab --require-ingress-dns
```

Sur **PowerShell**, exécuter `py -3 scripts/lab/verify.py --profile opsboard-lab --require-ingress-dns` à la place de la dernière commande. Le script valide l'état de Kubernetes sans le modifier ; il ne teste pas l'accès DNS du navigateur ni la haute disponibilité des volumes.

## D — Optionnel : K9s et commandes de reprise

```sh
# Si K9s est installé
k9s --context opsboard-lab

# En fin de journée (sortir de K9s avant)
minikube stop -p opsboard-lab

# Au retour
minikube start -p opsboard-lab
kubectl config use-context opsboard-lab
kubectl get nodes -o wide

# Si un composant est absent / non prêt
kubectl get pods -A
kubectl get events -A --sort-by=.lastTimestamp
```

## Références officielles

- [Minikube — installation](https://minikube.sigs.k8s.io/docs/start/)
- [Minikube — Traefik](https://minikube.sigs.k8s.io/docs/handbook/addons/traefik/)
- [Minikube — ingress-dns](https://minikube.sigs.k8s.io/docs/handbook/addons/ingress-dns/)
- [Kubernetes — kubectl](https://kubernetes.io/docs/tasks/tools/)
- [K9s — installation](https://github.com/derailed/k9s#installation)

Pour les *explications et limites*, lire le [runbook TP 0](TP0-lab-runbook.md).
