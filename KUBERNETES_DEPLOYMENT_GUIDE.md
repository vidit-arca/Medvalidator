# Kubernetes / Cloud UI Deployment Guide for Medical Bills App

This guide explains how to fill out your deployment dashboard based on the configuration we built for the Medical Bills application. You will need to run this process **twice** (once for the Backend, and once for the Frontend).

---

## 1. Deploying the Backend

### General Settings
*   **Target Cluster:** Select your desired cluster.
*   **Workload Type:** Select **Deployment** *(Stateless app with rolling updates)*.
*   **Namespace:** `default` (or whatever namespace you prefer).
*   **Name:** `medical-bills-backend`
*   **Replicas:** `1` *(You can scale this up later if needed)*.

### Container Configuration
*   **Image:** `viditk03/medical-bills-backend:latest`
*   **Container Port:** `8000` *(This is the port FastAPI listens on)*.

### Commands & Args
*   **Command:** *Leave blank* (It automatically uses the CMD from your Dockerfile).
*   **Args:** *Leave blank*

### Environment Variables
You must add the following environment variables exactly as we configured them in your Docker setup so the backend can connect to your server's PostgreSQL database and the Ollama instance:
*   **Name:** `DATABASE_URL` 
    *   **Value:** `postgresql://postgres:Password@123@<YOUR_DATABASE_IP>:5432/matrix`
*   **Name:** `OLLAMA_BASE_URL` 
    *   **Value:** `http://192.168.112.2:11434` *(Make sure this IP is reachable from your cluster)*

---

## 2. Deploying the Frontend

Once the backend is deployed, repeat the process to deploy the React frontend.

### General Settings
*   **Target Cluster:** Select your desired cluster.
*   **Workload Type:** Select **Deployment** *(Stateless app with rolling updates)*.
*   **Namespace:** `default` (Ensure it's in the same namespace as the backend).
*   **Name:** `medical-bills-frontend`
*   **Replicas:** `1`

### Container Configuration
*   **Image:** `viditk03/medical-bills-frontend:latest`
*   **Container Port:** `80` *(Nginx serves the frontend on port 80)*.

### Commands & Args
*   **Command:** *Leave blank*
*   **Args:** *Leave blank*

### Environment Variables
*   *Leave blank* (The frontend does not require environment variables at runtime).

---

## Next Steps (Networking)
After both workloads are deployed successfully:
1.  **Expose the Frontend:** You will need to create a **Service** or an **Ingress** pointing to the `medical-bills-frontend` workload on port 80 to make the UI accessible in your browser.
2.  **Seed the Database:** You can use your dashboard's "Execute Shell" or "Console" feature to hop into the running `medical-bills-backend` pod and execute the seed script: `python Tests/import_csv.py`.
