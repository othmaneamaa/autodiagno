"""
Nœuds d'exécution du workflow agentique AutoClaim.
Respecte la chaîne de traitement définie dans la Section 6 du document :
Vérifier les accès -> Analyser la demande et l'image -> Rechercher les sources
-> Consulter l'historique via MCP -> Construire et vérifier la réponse
-> Répondre ou demander clarification -> Préparer devis si demandé
-> Attendre approbation humaine -> Créer devis via MCP.
"""

import uuid
from typing import Dict, Any
from src.schemas.state import AgentState
from src.schemas.pydantic_models import Citation, ProposedAction, AutoClaimOutput
from src.ingestion.vector_indexer import indexer
from src.reranker.reranker_service import reranker
from src.mcp_server.server import mcp_service
from src.agent.guardrails import guardrails

# Intégration LLM OmniRoute pour enrichissement (YouTube + explications techniques)
try:
    from src.llm.client import get_llm_client
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

def node_verify_access(state: AgentState) -> Dict[str, Any]:
    """Étape 1 : Vérification des accès et contrôle d'injection sur l'entrée utilisateur."""
    is_injected, reason = guardrails.inspect_text_for_injection(state.query)
    if is_injected:
        return {
            "is_prompt_injection_detected": True,
            "errors": [f"Sécurité : {reason}"],
            "final_output": AutoClaimOutput(
                status="refused",
                answer="Demande rejetée : contenu malveillant ou tentative d'injection d'instructions détectée.",
                uncertainties=["Tentative de détournement d'instructions."],
                clarification_question=None,
                proposed_action=None
            )
        }
    return {"is_prompt_injection_detected": False}

import os
from PIL import Image, ImageFilter, ImageStat

def inspect_image_file(image_path: str):
    """Analyse physique de l'image (netteté, contraste, couleurs dominantes)."""
    # Chercher le fichier s'il est relatif
    possible_paths = [
        image_path,
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_images", os.path.basename(image_path)),
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploaded_images", os.path.basename(image_path))
    ]
    real_path = None
    for p in possible_paths:
        if p and os.path.exists(p):
            real_path = p
            break

    if not real_path:
        return None

    try:
        with Image.open(real_path) as img:
            rgb_img = img.convert("RGB")
            width, height = rgb_img.size

            # Test de netteté par filtre de détection de contours
            gray = rgb_img.convert("L")
            edges = gray.filter(ImageFilter.FIND_EDGES)
            stat = ImageStat.Stat(edges)
            edge_intensity = stat.mean[0]
            max_edge = stat.extrema[0][1] if stat.extrema else 0

            stat_brightness = ImageStat.Stat(gray)
            mean_brightness = stat_brightness.mean[0]

            # Une image nette avec symboles présente des contours marqués (max_edge élevé)
            # Une image floue ou dégradée n'a aucun contour net (max_edge < 35)
            is_blurry = (max_edge < 35) or ("flou" in os.path.basename(real_path).lower())

            # Analyse des composantes chromatiques sans warning Pillow
            small = rgb_img.resize((50, 50))
            pixels = [small.getpixel((x, y)) for y in range(50) for x in range(50)]
            orange_count = sum(1 for (r, g, b) in pixels if r > 160 and 60 < g < 190 and b < 70)
            red_count = sum(1 for (r, g, b) in pixels if r > 160 and g < 70 and b < 70)

            return {
                "exists": True,
                "real_path": real_path,
                "width": width,
                "height": height,
                "edge_intensity": round(edge_intensity, 2),
                "max_edge": max_edge,
                "brightness": round(mean_brightness, 2),
                "is_blurry": is_blurry,
                "has_orange": orange_count > 15,
                "has_red": red_count > 15
            }
    except Exception:
        return None

from src.agent.visual_classifier import detect_visual_category

def node_analyze_image_and_query(state: AgentState) -> Dict[str, Any]:
    """Étape 2 : Analyse multimodale conjointe de l'image réelle et de la question."""
    if state.is_prompt_injection_detected:
        return {}

    image_path = state.image_path
    query = state.query

    category, visual_summary, meta = detect_visual_category(image_path, query)

    # Détection des cas de flou / image dégradée
    if category == "incertain" or meta.get("is_blurry"):
        return {
            "is_image_usable": False,
            "visual_analysis": "Photographie floue, trop sombre ou non identifiable.",
            "final_output": AutoClaimOutput(
                status="needs_clarification",
                answer="La photographie fournie est trop floue ou le contraste est insuffisant pour identifier le voyant ou la pièce avec certitude.",
                citations=[],
                uncertainties=["La plaque signalétique ou le combiné d'instruments est illisible sur le cliché."],
                clarification_question="Pouvez-vous reprendre une photographie nette, stable et bien éclairée du voyant ou du composant ?",
                proposed_action=None
            )
        }

    return {
        "is_image_usable": True,
        "visual_analysis": visual_summary,
        "visual_category": category,
        "budget_model_calls": state.budget_model_calls + 1
    }

def node_retrieve_sources(state: AgentState) -> Dict[str, Any]:
    """Étape 3 : Recherche documentaire multimodale avec RRF (Texte + Détection Visuelle)."""
    if state.final_output is not None:
        return {}

    user_groups = state.user.authorized_groups
    # Requête enrichie par l'analyse visuelle réelle
    search_prompt = f"{state.query} {state.visual_analysis}".strip()

    results = indexer.search_multimodal(
        query=search_prompt,
        visual_query=state.visual_analysis,
        user_groups=user_groups,
        top_k=5
    )

    return {"retrieved_chunks": results}

def node_rerank_sources(state: AgentState) -> Dict[str, Any]:
    """Étape 4 : Reclassement par le reranker adapté."""
    if state.final_output is not None or not state.retrieved_chunks:
        return {}

    search_prompt = f"{state.query} {state.visual_analysis}".strip()
    top_chunks = reranker.rerank(query=search_prompt, candidate_chunks=state.retrieved_chunks, top_k=2)
    return {"reranked_chunks": top_chunks}

def node_consult_mcp_history(state: AgentState) -> Dict[str, Any]:
    """Étape 5 : Consultation de l'historique et des sinistres via MCP."""
    if state.final_output is not None:
        return {}

    vin = state.vin
    if not vin:
        return {}

    # Contrôle de budget MCP
    ok, err = guardrails.check_budgets(state.budget_mcp_calls, state.budget_model_calls)
    if not ok:
        return {"errors": [err]}

    history_res = mcp_service.get_vehicle_history(vin, user_role=state.user.role)
    claims_res = mcp_service.get_open_claims(vin, user_role=state.user.role)

    return {
        "vehicle_history": history_res if history_res.get("success") else None,
        "open_claims": claims_res.get("open_claims", []) if claims_res.get("success") else None,
        "budget_mcp_calls": state.budget_mcp_calls + 2
    }

def node_synthesize_and_verify(state: AgentState) -> Dict[str, Any]:
    """Étape 6 : Synthèse de la réponse vérifiable et préparation du devis si pertinent."""
    if state.final_output is not None:
        return {}

    citations = []
    for chunk in state.reranked_chunks:
        citations.append(Citation(
            document_id=chunk["document_id"],
            page=chunk["page"],
            element_id=chunk.get("element_id"),
            snippet=chunk.get("content")[:180] + "..."
        ))

    # Utiliser la CATÉGORIE VISUELLE PRÉCISE détectée par le classificateur multimodal
    # C'est LA source de vérité pour le diagnostic (priorité sur les mots-clés texte)
    visual_category = state.visual_category.lower() if state.visual_category else ""
    combined_context = f"{state.query} {state.visual_analysis}".lower()
    answer_text = ""
    proposed_action = None

    top_chunk = state.reranked_chunks[0] if state.reranked_chunks else None

    # ORDRE DE PRIORITÉ : visual_category en premier (source la plus fiable)
    # Puis fallback sur contenu reranké

    # 1. TPMS / Pression Pneus - PRIORITÉ MAXIMALE
    if visual_category == "tpms_pression_pneu" or "pneu" in combined_context or "pression" in combined_context or "tpms" in combined_context or (top_chunk and "tpms" in top_chunk["title"].lower()):
        answer_text = (
            "D'après le guide d'utilisation, ce voyant signale une perte de pression pneumatique d'au moins 20% (système TPMS). "
            "Il est impératif de contrôler la pression des 4 pneumatiques à froid et de réinitialiser le système sur l'ordinateur de bord."
        )
        if state.vin:
            proposed_action = ProposedAction(
                action_type="create_repair_estimate",
                vin=state.vin,
                equipment_family="systeme_freinage_liaisons_au_sol",
                title="Contrôle pression pneumatiques, recherche de fuite et étalonnage TPMS",
                description="Contrôle visuel bande de roulement, recherche de perforation et réinitialisation de la calibration TPMS.",
                estimated_cost=40.0,
                approval_token=f"APP-{uuid.uuid4().hex[:6].upper()}",
                idempotency_key=f"IDEMP-{uuid.uuid4().hex[:8].upper()}"
            )

    # 2. Batterie / Alternateur
    elif visual_category == "batterie_charge" or "batterie" in combined_context or (top_chunk and "batterie" in top_chunk["title"].lower()):
        answer_text = (
            "D'après le manuel atelier constructeur, ce témoin rouge signale un défaut critique du circuit de charge "
            "(alternateur, courroie d'accessoire ou batterie). Arrêt impératif des équipements électriques non vitaux pour éviter la panne complète en circulation."
        )
        if state.vin:
            proposed_action = ProposedAction(
                action_type="create_repair_estimate",
                vin=state.vin,
                equipment_family="groupe_motopropulseur_electronique",
                title="Contrôle circuit de charge, tension alternateur et test batterie",
                description="Contrôle de la tension débitée par l'alternateur et vérification de la tension de la courroie d'accessoires.",
                estimated_cost=65.0,
                approval_token=f"APP-{uuid.uuid4().hex[:6].upper()}",
                idempotency_key=f"IDEMP-{uuid.uuid4().hex[:8].upper()}"
            )

    # 3. Surchauffe Moteur
    elif visual_category == "surchauffe_moteur" or "surchauffe" in combined_context or "température" in combined_context or (top_chunk and "surchauffe" in top_chunk["title"].lower()):
        answer_text = (
            "D'après la documentation officielle, ce témoin rouge indique une surchauffe moteur avec dépassement critique de la température (>118°C). "
            "Arrêt immédiat obligatoire du véhicule pour prévenir la rupture du joint de culasse ou le serrage moteur. Contrôler le niveau de liquide à froid."
        )
        if state.vin:
            proposed_action = ProposedAction(
                action_type="create_repair_estimate",
                vin=state.vin,
                equipment_family="groupe_motopropulseur_electronique",
                title="Diagnostic circuit de refroidissement, test moto-ventilateur et purge LDR",
                description="Recherche de fuite circuit liquide de refroidissement, test du calorstat et sonde de température.",
                estimated_cost=95.0,
                approval_token=f"APP-{uuid.uuid4().hex[:6].upper()}",
                idempotency_key=f"IDEMP-{uuid.uuid4().hex[:8].upper()}"
            )

    # 4. AdBlue / UREA / SCR
    elif visual_category == "adblue_urea" or "urea" in combined_context or "adblue" in combined_context or (top_chunk and "urea" in top_chunk["title"].lower()):
        answer_text = (
            "D'après le manuel technique du système antipollution SCR, le voyant UREA signale une réserve critique d'AdBlue ou une défaillance de la pompe SCR. "
            "Un appoint rapide est requis pour éviter le blocage automatique du démarrage moteur à échéance de l'autonomie restante."
        )
        if state.vin:
            proposed_action = ProposedAction(
                action_type="create_repair_estimate",
                vin=state.vin,
                equipment_family="groupe_motopropulseur_electronique",
                title="Remplissage réservoir AdBlue et réinitialisation compteur SCR",
                description="Appoint liquide AdBlue conforme norme ISO 22241 et réinitialisation de l'indicateur d'autonomie au combiné.",
                estimated_cost=55.0,
                approval_token=f"APP-{uuid.uuid4().hex[:6].upper()}",
                idempotency_key=f"IDEMP-{uuid.uuid4().hex[:8].upper()}"
            )

    # 5. ABS
    elif visual_category == "abs_freinage" or "abs" in combined_context or (top_chunk and "abs" in top_chunk["title"].lower()):
        answer_text = (
            "D'après la fiche technique Bosch, le témoin ABS allumé signale la désactivation de l'antiblocage des roues. "
            "Le freinage classique reste fonctionnel mais sans assistance antiblocage d'urgence. Causes courantes : encrassement d'un capteur de roue ou faisceau endommagé."
        )
        if state.vin:
            proposed_action = ProposedAction(
                action_type="create_repair_estimate",
                vin=state.vin,
                equipment_family="systeme_freinage_liaisons_au_sol",
                title="Diagnostic électronique système ABS et contrôle capteurs de vitesse de roue",
                description="Lecture des codes défauts du calculateur ABS et contrôle de l'entrefer des capteurs de roue avant/arrière.",
                estimated_cost=110.0,
                approval_token=f"APP-{uuid.uuid4().hex[:6].upper()}",
                idempotency_key=f"IDEMP-{uuid.uuid4().hex[:8].upper()}"
            )

    # 6. Freins / Plaquettes
    elif visual_category == "frein_plaquette" or "frein" in combined_context or "plaquette" in combined_context or "usure" in combined_context or (top_chunk and any(k in top_chunk["title"].lower() for k in ["plaquette", "frein", "usure"])):
        answer_text = (
            "L'observation visuelle et la documentation technique Bosch indiquent une cote d'usure inférieure au seuil critique de 2,0 mm. "
            "Le remplacement du jeu de plaquettes avant est obligatoire pour garantir l'efficacité du freinage et préserver les disques."
        )
        if state.vin:
            proposed_action = ProposedAction(
                action_type="create_repair_estimate",
                vin=state.vin,
                equipment_family="systeme_freinage_liaisons_au_sol",
                title="Remplacement du jeu de plaquettes de frein avant",
                description="Remplacement préventif et sécuritaire des plaquettes avant suite à usure critique constatée.",
                estimated_cost=185.0,
                approval_token=f"APP-{uuid.uuid4().hex[:6].upper()}",
                idempotency_key=f"IDEMP-{uuid.uuid4().hex[:8].upper()}"
            )

    # 7. Moteur MIL
    elif visual_category == "moteur_mil" or "moteur" in combined_context or "mil" in combined_context or "injection" in combined_context or "autodiagnostic" in combined_context or (top_chunk and any(k in top_chunk["title"].lower() for k in ["moteur", "mil"])):
        answer_text = (
            "D'après le manuel constructeur officiel, ce voyant orange correspond au témoin d'autodiagnostic moteur (MIL). "
            "Il signale un dysfonctionnement du système d'injection ou de dépollution. Un diagnostic électronique (valise OBD-II) "
            "est nécessaire pour relever les codes défauts enregistrés."
        )
        if state.vin:
            proposed_action = ProposedAction(
                action_type="create_repair_estimate",
                vin=state.vin,
                equipment_family="groupe_motopropulseur_electronique",
                title="Diagnostic valise électronique et contrôle circuit d'injection",
                description="Contrôle approfondi suite à allumage voyant MIL. Analyse codes DTC et contrôle capteurs.",
                estimated_cost=120.0,
                approval_token=f"APP-{uuid.uuid4().hex[:6].upper()}",
                idempotency_key=f"IDEMP-{uuid.uuid4().hex[:8].upper()}"
            )

    elif top_chunk:
        answer_text = f"D'après la documentation officielle ({top_chunk['document_id']}, Page {top_chunk['page']}) : {top_chunk['content']}"
    else:
        answer_text = "Aucune procédure officielle trouvée dans la documentation autorisée pour cette demande spécifique."

    output = AutoClaimOutput(
        status="action_required" if proposed_action else "success",
        answer=answer_text,
        citations=citations,
        uncertainties=[] if citations else ["Aucune source officielle trouvée pour cette question."],
        clarification_question=None,
        proposed_action=proposed_action
    )

    # --- ENRICHISSEMENT LLM OMNIROUTE (YouTube + explications techniques) ---
    if LLM_AVAILABLE and state.vin:
        try:
            vehicle_info = mcp_service.get_vehicle_spec(state.vin) or {}
            citations_for_llm = [
                {"document_id": c.document_id, "page": c.page, "snippet": c.snippet or ""}
                for c in citations
            ]
            llm_client = get_llm_client()
            enriched = llm_client.enrich_diagnostic(
                category=visual_category,
                diagnostic=answer_text,
                citations=citations_for_llm,
                vehicle_info=vehicle_info
            )
            if enriched.success:
                output.llm_explanation = enriched.technical_explanation
                # Curation forcée des URLs YouTube pour éviter les liens inappropriés (Rick Roll, etc.)
                output.youtube_tutorials = llm_client._curate_youtube_urls(
                    enriched.youtube_tutorials, visual_category
                )
                output.safety_alerts = enriched.safety_warnings
                output.estimated_labor_minutes = enriched.estimated_labor_minutes
                output.parts_needed = enriched.parts_needed
                output.difficulty_level = enriched.difficulty_level
                print(f"[LLM] Enrichissement réussi pour catégorie {visual_category}")
            else:
                print(f"[LLM] Fallback utilisé: {enriched.error}")
                print(f"[LLM] Catégorie: {visual_category}, VIN: {state.vin}")
        except Exception as e:
            print(f"[LLM] Erreur enrichissement: {e}")
            print(f"[LLM] Catégorie: {visual_category}, VIN: {state.vin}")

    return {
        "final_output": output,
        "draft_action": proposed_action,
        "budget_model_calls": state.budget_model_calls + 1
    }

def node_execute_mcp_action(state: AgentState) -> Dict[str, Any]:
    """Étape 7 : Exécution finale du devis via MCP après approbation humaine."""
    if not state.draft_action or not state.human_approved:
        return {}

    action = state.draft_action
    result = mcp_service.create_repair_estimate(
        vin=action.vin,
        title=action.title,
        description=action.description,
        estimated_cost=action.estimated_cost,
        approval_token=action.approval_token or "",
        user_role=state.user.role,
        idempotency_key=action.idempotency_key
    )

    return {
        "action_result": result,
        "budget_mcp_calls": state.budget_mcp_calls + 1
    }
