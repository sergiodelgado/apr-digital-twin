import type { NextConfig } from "next";

// URL de la API FastAPI del gemelo digital. En local apunta al uvicorn en :8000.
// Se puede sobrescribir con la variable de entorno APR_API_URL.
const API_URL = process.env.APR_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Proxy same-origin: el navegador llama a /api/apr/* (mismo origen que el front)
  // y Next.js lo reenvía a la API FastAPI. Así se evita cualquier problema de CORS
  // sin tener que modificar el backend.
  async rewrites() {
    return [
      {
        source: "/api/apr/:path*",
        destination: `${API_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
