import os
import socket
import time

import psycopg2
from flask import Flask
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "tutorial")
DB_USER = os.environ.get("DB_USER", "tutorial_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
WELCOME_MESSAGE = os.environ.get("WELCOME_MESSAGE", "Bonjour !")
POD_NAMESPACE = os.environ.get("POD_NAMESPACE", "default")


def get_peer_info():
    """Liste les Pods de l'appli via l'API Kubernetes -- demande des
    permissions RBAC (voir le ServiceAccount/Role du chart)."""
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(POD_NAMESPACE, label_selector="app=web")
        names = sorted(p.metadata.name for p in pods.items)
        return f"{len(names)} Pod(s) vu(s) via l'API Kubernetes : {', '.join(names)}"
    except ApiException as exc:
        return f"Appel à l'API Kubernetes refusé par RBAC (HTTP {exc.status}) -- voir STEP.md."
    except Exception as exc:  # pas de cluster accessible, ex: run en local
        return f"API Kubernetes indisponible : {exc}"


def get_connection():
    last_error = None
    for _ in range(10):
        try:
            return psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=3,
            )
        except psycopg2.OperationalError as exc:
            last_error = exc
            time.sleep(2)
    raise last_error


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS visits ("
            "id SERIAL PRIMARY KEY, created_at TIMESTAMPTZ DEFAULT now())"
        )
    conn.commit()


@app.route("/")
def index():
    conn = get_connection()
    try:
        ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute("INSERT INTO visits DEFAULT VALUES")
            cur.execute("SELECT count(*) FROM visits")
            count = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    peer_info = get_peer_info()

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Tuto Kubernetes — Étape 12</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; background: #0b1020; color: #e8eefc; display: flex; height: 100vh; align-items: center; justify-content: center; margin: 0; }}
    .card {{ background: #161b2e; padding: 2.5rem 3rem; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); text-align: center; max-width: 36rem; }}
    h1 {{ margin-top: 0; color: #7dd3fc; }}
    code {{ background: #0b1020; padding: 0.2rem 0.5rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Étape 12 : RBAC</h1>
    <p>{WELCOME_MESSAGE}</p>
    <p>Nombre de visites (stocké dans Postgres) : <strong>{count}</strong></p>
    <p>Répondu par le Pod : <code>{socket.gethostname()}</code></p>
    <p>{peer_info}</p>
  </div>
</body>
</html>"""


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
