#!/usr/bin/env python3
"""Read-only validation of the INFAL127 three-node Kubernetes training cluster.

Requires Python >=3.10 and kubectl on PATH. Runs no mutating kubectl commands.
Checks resource presence and readiness; it does NOT prove NetworkPolicy enforcement,
Ingress DNS resolution from the host, or volume failover across nodes.
"""

import argparse
import json
import subprocess
import sys


def kubectl(*args):
    proc = subprocess.run(
        ["kubectl", *args], capture_output=True, text=True, check=False, timeout=40
    )
    if proc.returncode:
        raise RuntimeError(f"kubectl {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


def items(resource, *flags):
    return json.loads(kubectl("get", resource, *flags, "-o", "json"))["items"]


def is_ready(pod):
    return any(
        c.get("type") == "Ready" and c.get("status") == "True"
        for c in pod.get("status", {}).get("conditions", [])
    )


def named(resources, term):
    return [obj for obj in resources if term in obj["metadata"]["name"]]


def check(name, passed, reason):
    print(f"{'OK' if passed else 'FAIL'}  {name} — {reason}")
    return int(not passed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="opsboard-lab")
    parser.add_argument("--require-ingress-dns", action="store_true")
    args = parser.parse_args()

    context = kubectl("config", "current-context").strip()
    nodes = items("nodes")
    pods = items("pods", "-A")
    classes = items("storageclasses")
    drivers = items("csidrivers")
    ingressclasses = items("ingressclasses")
    ns = items("namespaces")
    fail = 0
    names = {x["metadata"]["name"] for x in nodes}
    ready_nodes = {
        x["metadata"]["name"] for x in nodes
        if any(y.get("type") == "Ready" and y.get("status") == "True"
               for y in x.get("status", {}).get("conditions", []))
    }
    control_planes = [
        x for x in nodes if
        "node-role.kubernetes.io/control-plane" in x["metadata"].get("labels", {})
        or "node-role.kubernetes.io/master" in x["metadata"].get("labels", {})
    ]
    fail += check("Contexte kubectl", context == args.profile, context)
    fail += check("Trois nœuds", len(nodes) == 3 and len(ready_nodes) == 3,
                  f"Ready={len(ready_nodes)}/{len(nodes)}")
    fail += check("Un control-plane", len(control_planes) == 1,
                  f"control-plane={len(control_planes)}")
    runtimes = {x.get("status", {}).get("nodeInfo", {}).get(
        "containerRuntimeVersion", "") for x in nodes}
    fail += check("Runtime containerd", len(runtimes) == 1 and
                  next(iter(runtimes), "").startswith("containerd://"),
                  ", ".join(sorted(runtimes)))

    calico = [p for p in pods if "calico-node" in p["metadata"]["name"]]
    calico_ready = {p.get("spec", {}).get("nodeName") for p in calico if is_ready(p)}
    fail += check("Calico sur les 3 nœuds", names == calico_ready,
                  f"Calico ready sur {len(calico_ready)}/3 nœuds")
    core = [p for p in pods if p["metadata"]["name"].startswith("coredns-")]
    fail += check("CoreDNS", bool(core) and all(is_ready(p) for p in core),
                  f"{sum(is_ready(p) for p in core)}/{len(core)} pods Ready")

    traefik = [p for p in pods if p["metadata"]["name"].startswith("traefik-")
               and p["metadata"].get("namespace") == "kube-system"]
    fail += check("Traefik", bool(traefik) and all(is_ready(p) for p in traefik),
                  f"{sum(is_ready(p) for p in traefik)}/{len(traefik)} pods Ready")
    ing = {x["metadata"]["name"] for x in ingressclasses}
    fail += check("IngressClass traefik", "traefik" in ing, str(sorted(ing)))
    cls = {x["metadata"]["name"]: x for x in classes}
    fail += check("StorageClass standard", "standard" in cls, str(sorted(cls)))
    fail += check("CSI Hostpath StorageClass", cls.get("csi-hostpath-sc", {}).get(
        "provisioner") == "hostpath.csi.k8s.io", str(sorted(cls)))
    csis = {x["metadata"]["name"] for x in drivers}
    fail += check("CSI Hostpath Driver", "hostpath.csi.k8s.io" in csis,
                  str(sorted(csis)))
    fail += check("Namespace opsboard", any(
        x["metadata"]["name"] == "opsboard" for x in ns), "opsboard")
    dns = [p for p in pods if "ingress-dns" in p["metadata"]["name"]]
    dns_up = bool(dns) and all(is_ready(p) for p in dns)
    if args.require_ingress_dns:
        fail += check("Addon ingress-dns", dns_up,
                      f"{sum(is_ready(p) for p in dns)}/{len(dns)} pods Ready")
    else:
        print(f"INFO  ingress-dns (optionnel) — {len(dns)} pod(s) détecté(s)")
    print("NOTE  DNS du poste, réseau Windows/macOS, PVC et NetworkPolicy "
          "nécessitent une recette distincte.")
    return 1 if fail else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.TimeoutExpired) as e:
        print(f"FAIL  Erreur de validation : {e}", file=sys.stderr)
        sys.exit(2)
