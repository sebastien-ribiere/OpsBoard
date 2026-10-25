"use strict";

async function refresh() {
  const error = document.getElementById("error");
  error.textContent = "";
  try {
    const responses = await Promise.all([
      fetch("/api/status", { cache: "no-store" }),
      fetch("/api/version", { cache: "no-store" }),
    ]);
    if (responses.some((response) => !response.ok)) {
      throw new Error("L'API est indisponible.");
    }
    const [status, version] = await Promise.all(responses.map((r) => r.json()));
    document.getElementById("banner").textContent = status.message;
    document.getElementById("environment").textContent = status.environment;
    document.getElementById("version").textContent = version.version;
    const list = document.getElementById("components");
    list.replaceChildren();
    for (const component of status.components) {
      const item = document.createElement("li");
      item.textContent = component.name + " : " + component.status;
      list.appendChild(item);
    }
  } catch (err) {
    error.textContent = "Impossible de joindre l'API : " + err.message;
  }
}

document.getElementById("refresh").addEventListener("click", refresh);
refresh();
