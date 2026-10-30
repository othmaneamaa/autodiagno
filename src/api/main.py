"""
API FastAPI pour AutoClaim.
Expose les endpoints de diagnostic, d'authentification et de validation humaine (Human-in-the-Loop).
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.schemas.pydantic_models import UserContext, AutoClaimOutput
from src.schemas.state import AgentState
from src.agent.graph import agent_graph
from src.mcp_server.server import mcp_service
from src.reranker.evaluate_reranker import run_comparative_benchmark
from src.api.auth_endpoints import router as auth_router
from src.auth.auth_service import auth_service

app = FastAPI(
    title="AutoClaim API",
    version="1.0.0",
    description="API pour l'assistant multimodal et agentique de diagnostic automobile"
)

# Configuration CORS pour Streamlit / frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    vin: Optional[str] = None
    image_path: Optional[str] = None
    user_id: str = "TECH_01"
    user_role: str = "technicien"
    user_groups: List[str] = ["groupe_standard"]

class ApprovalRequest(BaseModel):
    vin: str
    title: str
    description: str
    estimated_cost: float
    approval_token: str
    user_role: str = "expert_valideur"
    idempotency_key: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "AutoClaim API"}

@app.post("/api/chat", response_model=AutoClaimOutput)
def chat_endpoint(req: ChatRequest):
    """
    Exécute le workflow agentique LangGraph complet :
    Vérification sécurité -> VLM -> RAG Multimodal -> Reranking -> MCP -> Synthèse Pydantic.
    """
    user_ctx = UserContext(
        user_id=req.user_id,
        role=req.user_role,
        authorized_groups=req.user_groups
    )

    initial_state = AgentState(
        user=user_ctx,
        query=req.query,
        vin=req.vin,
        image_path=req.image_path,
        human_approved=False
    )

    final_state_dict = agent_graph.invoke(initial_state)

    output = final_state_dict.get("final_output")
    if not output:
        raise HTTPException(status_code=500, detail="Échec de génération de la réponse agentique.")

    return output

@app.post("/api/claims/approve")
def approve_estimate_endpoint(req: ApprovalRequest):
    """
    Point de terminaison Human-in-the-Loop :
    Un expert humain valide le brouillon d'estimation avec son token d'approbation.
    """
    result = mcp_service.create_repair_estimate(
        vin=req.vin,
        title=req.title,
        description=req.description,
        estimated_cost=req.estimated_cost,
        approval_token=req.approval_token,
        user_role=req.user_role,
        idempotency_key=req.idempotency_key
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Erreur de validation."))

    return result

# Enregistrement des routes d'authentification professionnelle
app.include_router(auth_router, prefix="/api")

@app.get("/api/vehicles")
def list_vehicles_endpoint(brand: Optional[str] = None):
    """Liste tous les véhicules du parc avec leurs fiches techniques."""
    vehicles = mcp_service.get_all_vehicles()
    if brand:
        brand_lower = brand.lower()
        vehicles = [v for v in vehicles if v.get("brand", "").lower() == brand_lower or v.get("model", "").lower().startswith(brand_lower)]
    return {"total": len(vehicles), "vehicles": vehicles}

@app.get("/api/vehicles/{vin}/spec")
def get_vehicle_spec_endpoint(vin: str):
    """Consulte la fiche technique détaillée d'un véhicule spécifique."""
    spec = mcp_service.get_vehicle_spec(vin)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Véhicule {vin} introuvable.")
    return spec

@app.get("/api/vehicles/{vin}/history")
def get_vehicle_history_endpoint(vin: str, role: str = "technicien"):
    """Consultation directe de l'historique d'un véhicule via le serveur MCP."""
    res = mcp_service.get_vehicle_history(vin, user_role=role)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error"))
    return res

@app.get("/api/benchmark/reranker")
def get_reranker_benchmark():
    """Retourne la comparaison scientifique des performances (Sans Reranker vs Base vs Adapté)."""
    return run_comparative_benchmark()
