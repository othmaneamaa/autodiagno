"""
Client LLM compatible OpenAI / OmniRoute pour AutoClaim.
Appelle l'API de chat completions pour enrichir le diagnostic avec :
- Explication technique approfondie
- Vidéos YouTube tutoriels sélectionnées
- Alertes sécurité supplémentaires
- Temps main-d'œuvre estimé
- Pièces nécessaires
- Niveau de difficulté
"""

import os
import json
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EnrichedResult:
    """Résultat d'enrichissement LLM pour un diagnostic automobile."""
    technical_explanation: str = ""
    youtube_tutorials: List[Dict[str, str]] = field(default_factory=list)
    safety_warnings: List[str] = field(default_factory=list)
    estimated_labor_minutes: int = 60
    parts_needed: List[str] = field(default_factory=list)
    difficulty_level: str = "Moyen"
    raw_response: str = ""
    success: bool = False
    error: Optional[str] = None


class LLMClient:
    """Client HTTP vers l'API chat completions (OmniRoute / OpenAI compatible)."""

    def __init__(self, config_path: str = "config/llm_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        llm_cfg = self.config["llm"]

        self.base_url = llm_cfg["base_url"].rstrip("/")
        self.api_key = llm_cfg["api_key"]
        self.default_model = llm_cfg["default_model"]
        self.timeout = llm_cfg.get("timeout_seconds", 30)
        self.system_prompt = llm_cfg.get("system_prompt", "")

        custom_headers = llm_cfg.get("routing", {}).get("custom_headers", {})

        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                **custom_headers
            },
            timeout=self.timeout
        )

    def _load_config(self, path: str) -> Dict[str, Any]:
        import yaml
        cfg_file = Path(path)
        if not cfg_file.is_absolute():
            # Chercher relatif à la racine du projet
            project_root = Path(__file__).resolve().parents[2]
            cfg_file = project_root / path
        if not cfg_file.exists():
            raise FileNotFoundError(f"Fichier de config LLM introuvable : {cfg_file}")
        with open(cfg_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def enrich_diagnostic(
        self,
        category: str,
        diagnostic: str,
        citations: List[Dict[str, Any]],
        vehicle_info: Dict[str, Any]
    ) -> EnrichedResult:
        """
        Appelle le LLM pour enrichir un diagnostic AutoClaim.

        Args:
            category: Catégorie détectée (tpms_pression_pneu, batterie_charge, etc.)
            diagnostic: Texte du diagnostic déjà généré par le workflow
            citations: Citations des sources officielles (document_id, page, snippet)
            vehicle_info: Infos du véhicule (brand, model, engine, fuel_type, year, mileage_km, vin)
        """
        prompt = self._build_prompt(category, diagnostic, citations, vehicle_info)

        payload = {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            # max_tokens retiré : non supporté uniformément par tous les modèles Groq
        }

        try:
            # Appel endpoint OpenAI compatible (Groq, OpenAI, Azure, etc.)
            response = self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content, category)
        except httpx.HTTPStatusError as e:
            # Afficher le détail de l'erreur retournée par Groq
            detail = ""
            try:
                detail = e.response.text[:500]
            except Exception:
                pass
            print(f"[LLM] Erreur appel API: {e} | Détail: {detail}")
            return self._fallback(category, str(e))
        except Exception as e:
            print(f"[LLM] Erreur appel API: {e}")
            return self._fallback(category, str(e))

    def _build_prompt(
        self,
        category: str,
        diagnostic: str,
        citations: List[Dict[str, Any]],
        vehicle_info: Dict[str, Any]
    ) -> str:
        """Construit le prompt utilisateur avec contexte véhicule et citations."""
        cit_lines = "\n".join([
            f"- {c.get('document_id', 'N/A')} p.{c.get('page', 'N/A')}: {c.get('snippet', '')[:200]}"
            for c in citations[:5]
        ]) or "Aucune citation disponible."

        vin = vehicle_info.get("vin", "N/A")
        brand = vehicle_info.get("brand", "N/A")
        model = vehicle_info.get("model", "N/A")
        engine = vehicle_info.get("engine", "N/A")
        fuel = vehicle_info.get("fuel_type", "N/A")
        year = vehicle_info.get("year", "N/A")
        mileage = vehicle_info.get("mileage_km", "N/A")

        return f"""VÉHICULE :
- VIN : {vin}
- Marque / Modèle : {brand} {model}
- Année : {year}
- Kilométrage : {mileage} km
- Moteur : {engine}
- Carburant : {fuel}

CATÉGORIE DE PANNE DÉTECTÉE : {category}

DIAGNOSTIC DE BASE (workflow agentique) :
{diagnostic}

SOURCES OFFICIELLES CITÉES (manuels constructeur) :
{cit_lines}

Générez maintenant le JSON d'enrichissement complet avec :
1. Une explication technique détaillée (niveau professionnel)
2. Des liens YouTube vers des tutoriels pertinents (chaînes officielles préférées)
3. Les alertes de sécurité spécifiques à cette intervention
4. Le temps de main-d'œuvre estimé (barème constructeur)
5. La liste des pièces nécessaires avec références si connues
6. Le niveau de difficulté (Facile / Moyen / Difficile / Expert)"""

    def _parse_response(self, content: str, category: str = "unknown") -> EnrichedResult:
        try:
            cleaned = content.strip()

            # Retirer les balises markdown ```json ... ``` ou ``` ... ```
            if cleaned.startswith("```"):
                # Trouver la fin du premier bloc de code
                first_newline = cleaned.find("\n")
                if first_newline != -1:
                    cleaned = cleaned[first_newline + 1:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

            # Stratégie robuste : extraire le JSON entre le premier { et le dernier }
            first_brace = cleaned.find("{")
            last_brace = cleaned.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = cleaned[first_brace : last_brace + 1]
            else:
                json_str = cleaned

            data = json.loads(json_str)
            return EnrichedResult(
                technical_explanation=data.get("technical_explanation", ""),
                youtube_tutorials=data.get("youtube_tutorials", []),
                safety_warnings=data.get("safety_warnings", []),
                estimated_labor_minutes=data.get("estimated_labor_minutes", 60),
                parts_needed=data.get("parts_needed", []),
                difficulty_level=data.get("difficulty_level", "Moyen"),
                raw_response=content,
                success=True
            )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[LLM] Erreur parsing JSON: {e}")
            print(f"[LLM] Réponse reçue: {content[:500]}...")
            # Le LLM a répondu en texte libre, on l'utilise comme explication technique
            # et on ajoute des liens YouTube curatés selon la catégorie (pas de Rick Roll)
            youtube_tutorials = self._get_youtube_fallbacks(category)
            return EnrichedResult(
                technical_explanation=content.strip() if content else "",
                youtube_tutorials=youtube_tutorials,
                safety_warnings=["Consultez le manuel constructeur pour la procédure officielle."],
                estimated_labor_minutes=60,
                parts_needed=[],
                difficulty_level="Moyen",
                raw_response=content,
                success=True,
                error=None
            )

    def _curate_youtube_urls(self, youtube_tutorials: List[Dict[str, str]], category: str) -> List[Dict[str, str]]:
        """Remplace toutes les URLs YouTube par des liens de recherche curatés (jamais de Rick Roll)."""
        curated = self._get_youtube_fallbacks(category)
        # On garde les titres du LLM mais on force des URLs de recherche YouTube sûres
        for i, yt in enumerate(youtube_tutorials[: len(curated)]):
            curated[i]["title"] = yt.get("title", curated[i]["title"])
        return curated

    def _get_youtube_fallbacks(self, category: str) -> List[Dict[str, str]]:
        """Retourne des liens YouTube par défaut selon la catégorie de panne."""
        youtube_fallbacks = {
            "tpms_pression_pneu": [
                {"title": "TPMS Reset - Pression des pneus", "url": "https://www.youtube.com/results?search_query=TPMS+reset+pression+pneus+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Gonflage et vérification pneus", "url": "https://www.youtube.com/results?search_query=comment+gonfler+pneus+voiture+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "batterie_charge": [
                {"title": "Test alternateur et batterie", "url": "https://www.youtube.com/results?search_query=test+alternateur+batterie+voiture+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Remplacement batterie automobile", "url": "https://www.youtube.com/results?search_query=remplacement+batterie+auto+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "surchauffe_moteur": [
                {"title": "Surchauffe moteur diagnostic", "url": "https://www.youtube.com/results?search_query=surchauffe+moteur+diagnostic+refroidissement+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Remplacement calorstat et purge LDR", "url": "https://www.youtube.com/results?search_query=remplacement+calorstat+purge+liquide+refroidissement", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "adblue_urea": [
                {"title": "AdBlue UREA SCR système", "url": "https://www.youtube.com/results?search_query=AdBlue+UREA+SCR+reservoir+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Réinitialisation système SCR AdBlue", "url": "https://www.youtube.com/results?search_query=reinitialisation+SCR+AdBlue+témoin+allumé", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "abs_freinage": [
                {"title": "Diagnostic ABS capteurs de roue", "url": "https://www.youtube.com/results?search_query=diagnostic+ABS+capteurs+roue+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Témoin ABS allumé causes solutions", "url": "https://www.youtube.com/results?search_query=témoin+ABS+allumé+causes+solutions+auto", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "frein_plaquette": [
                {"title": "Remplacement plaquettes de frein", "url": "https://www.youtube.com/results?search_query=remplacement+plaquettes+frein+avant+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Usure plaquettes cote minimale", "url": "https://www.youtube.com/results?search_query=usure+plaquettes+frein+cote+minimale+mm", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "moteur_mil": [
                {"title": "Voyant MIL moteur diagnostic OBD-II", "url": "https://www.youtube.com/results?search_query=voyant+MIL+moteur+diagnostic+OBD+II+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Codes défauts moteur valise OBD", "url": "https://www.youtube.com/results?search_query=codes+defauts+moteur+valise+OBD+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"}
            ]
        }
        return youtube_fallbacks.get(category, [
            {"title": "Tutoriel réparation automobile", "url": "https://www.youtube.com/results?search_query=tutoriel+reparation+automobile+témoin+tableau+bord", "channel": "Recherche YouTube", "duration": "N/A"}
        ])

    def _fallback(self, category: str, error: Optional[str] = None) -> EnrichedResult:
        """Réponse de secours sans appel LLM (si API indisponible)."""
        youtube_fallbacks = {
            "tpms_pression_pneu": [
                {"title": "TPMS Reset - Pression des pneus", "url": "https://www.youtube.com/results?search_query=TPMS+reset+pression+pneus+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Gonflage et vérification pneus", "url": "https://www.youtube.com/results?search_query=comment+gonfler+pneus+voiture+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "batterie_charge": [
                {"title": "Test alternateur et batterie", "url": "https://www.youtube.com/results?search_query=test+alternateur+batterie+voiture+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Remplacement batterie automobile", "url": "https://www.youtube.com/results?search_query=remplacement+batterie+auto+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "surchauffe_moteur": [
                {"title": "Surchauffe moteur diagnostic", "url": "https://www.youtube.com/results?search_query=surchauffe+moteur+diagnostic+refroidissement+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Remplacement calorstat et purge LDR", "url": "https://www.youtube.com/results?search_query=remplacement+calorstat+purge+liquide+refroidissement", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "adblue_urea": [
                {"title": "AdBlue UREA SCR système", "url": "https://www.youtube.com/results?search_query=AdBlue+UREA+SCR+reservoir+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Réinitialisation système SCR AdBlue", "url": "https://www.youtube.com/results?search_query=reinitialisation+SCR+AdBlue+témoin+allumé", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "abs_freinage": [
                {"title": "Diagnostic ABS capteurs de roue", "url": "https://www.youtube.com/results?search_query=diagnostic+ABS+capteurs+roue+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Témoin ABS allumé causes solutions", "url": "https://www.youtube.com/results?search_query=témoin+ABS+allumé+causes+solutions+auto", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "frein_plaquette": [
                {"title": "Remplacement plaquettes de frein", "url": "https://www.youtube.com/results?search_query=remplacement+plaquettes+frein+avant+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Usure plaquettes cote minimale", "url": "https://www.youtube.com/results?search_query=usure+plaquettes+frein+cote+minimale+mm", "channel": "Recherche YouTube", "duration": "N/A"}
            ],
            "moteur_mil": [
                {"title": "Voyant MIL moteur diagnostic OBD-II", "url": "https://www.youtube.com/results?search_query=voyant+MIL+moteur+diagnostic+OBD+II+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"},
                {"title": "Codes défauts moteur valise OBD", "url": "https://www.youtube.com/results?search_query=codes+defauts+moteur+valise+OBD+tutoriel", "channel": "Recherche YouTube", "duration": "N/A"}
            ]
        }

        return EnrichedResult(
            technical_explanation=(
                "Diagnostic basé sur le manuel constructeur officiel. "
                "L'enrichissement IA n'a pas pu être généré (service LLM indisponible). "
                "Consultez les citations documentaires pour la procédure officielle."
            ),
            youtube_tutorials=youtube_fallbacks.get(category, [
                {"title": "Tutoriel réparation automobile", "url": "https://www.youtube.com/results?search_query=tutoriel+reparation+automobile+témoin+tableau+bord", "channel": "Recherche YouTube", "duration": "N/A"}
            ]),
            safety_warnings=[
                "Respecter les procédures constructeur",
                "Porter les EPI adaptés (gants, lunettes)",
                "Vérifier l'absence de pression résiduelle avant intervention"
            ],
            estimated_labor_minutes=60,
            parts_needed=[],
            difficulty_level="Moyen",
            raw_response="",
            success=False,
            error=error
        )


# Instance globale (initialisée au premier appel)
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Retourne l'instance singleton du client LLM."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
