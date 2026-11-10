{{- define "opsboard.securityContext" -}}
readOnlyRootFilesystem: true
allowPrivilegeEscalation: false
runAsNonRoot: true
capabilities:
  drop: ["ALL"]
{{- end -}}
{{- define "opsboard.probes" -}}
readinessProbe:
  httpGet:
    path: {{ .ready }}
    port: http
  initialDelaySeconds: 3
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3
livenessProbe:
  httpGet:
    path: {{ .live }}
    port: http
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3
{{- end -}}
