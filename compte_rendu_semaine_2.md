# COMPTE RENDU — SEMAINE 2
## Projet AutoDiag  — Assistant Multimodal et Agentique Automobile

**Étudiant :** Othmane Amaadour  
**Date :** 07 novembre 2026  


---

## 1. OBJECTIFS DE LA SEMAINE 2 (CONCEPTION & PLANIFICATION)

La semaine 2 a été consacrée à la **conception architecturale et à la planification** du projet. Aucun développement fonctionnel complet n'a encore été réalisé à ce stade ; l'accent a été mis sur la définition des spécifications techniques qui guideront la réalisation lors des semaines suivantes.

| # | Objectif | Détail | Statut |
|---|----------|--------|--------|
| 1 | Conception de l'architecture globale | Interface, API, workflow agentique, RAG, serveur MCP | ✅ Conçu |
| 2 | Définition du schéma de sortie Pydantic | Modèles de données stricts pour l'état de l'agent et la sortie finale | ✅ Conçu |
| 3 | Définition des rôles RBAC | Technicien, Expert Valideur, Gestionnaire Flotte, Admin | ✅ Conçu |
| 4 | Choix des modèles et du dataset | LLM OmniRoute, BGE-M3, CLIP, Qdrant, manuels PDF, images | ✅ Planifié |
| 5 | Dossier d'architecture et diagrammes | UML / séquence, schéma des données Qdrant + JSON | ✅ Planifié |

---

## 2. TRAVAUX DE CONCEPTION RÉALISÉS

### 2.1 Conception de l'architecture logicielle

Une architecture **modulaire en couches** a été définie pour séparer les préoccupations :

| Couche | Composant | Rôle dans la conception |
|--------|-----------|------------------------|
| Présentation | Interface Streamlit (`src/ui/app.py`) | Authentification, formulaires, affichage résultats |
| Orchestration | Workflow LangGraph (`src/agent/graph.py`, `src/agent/nodes.py`) | Chaîne de traitement agentique |
| Métier | RAG, Serveur MCP, Pricing/Scraping | Recherche documentaire, historique véhicules, prix pièces |
| Infrastructure | Qdrant (vectoriel), JSON (cache prix), MCP Database | Stockage et récupération des données |

**Flux de données conçu :**

```
Interface Streamlit → LangGraph (verify → analyze → retrieve → rerank → synthesize) → RAG Qdrant + MCP Serveur + Pricing
```

---

### 2.2 Schéma de sortie Pydantic (conception)

Les modèles de données stricts ont été définis pour typer l'état de l'agent et la sortie finale (fichier `src/schemas/pydantic_models.py`) :

- **`UserContext`** : `user_id`, `role`, `authorized_groups`
- **`AgentState`** : État du graphe LangGraph (query, vin, image_path, flags d'injection, visibilité image, chunks, historique, output final, action proposée, budgets)
- **`Citation`** : `document_id`, `page`, `element_id`, `snippet`
- **`ProposedAction`** : `action_type`, `vin`, `equipment_family`, `title`, `description`, `estimated_cost`, `approval_token`, `idempotency_key`
- **`AutoClaimOutput`** : `status`, `answer`, `citations`, `uncertainties`, `proposed_action`, `part_prices`, `total_parts_cost_mad`, `llm_explanation`, `youtube_tutorials`, `safety_alerts`, `estimated_labor_minutes`, `parts_needed`, `difficulty_level`
- **`PartPriceInfo`** : `site_name`, `site_url`, `product_name`, `product_brand`, `product_category`, `price_mad`, `currency`, `last_updated`, `in_stock`, `scrape_timestamp`

---

### 2.3 Modèle RBAC (conception)

Quatre rôles ont été définis avec leurs permissions respectives :

| Rôle | Permissions prévues |
|------|---------------------|
| `technicien` | Lancer diagnostics, consulter historique VIN, préparer devis (brouillon) |
| `expert_valideur` | Approuver/refuser les devis (Human-in-the-Loop), créer devis via MCP |
| `gestionnaire_flotte` | Consulter parc véhicules, statistiques d'interventions |
| `admin` | Accès complet, gestion utilisateurs, configuration système |

Le contrôle d'accès sera implémenté dans `src/auth/auth_service.py` et `src/mcp_server/server.py`.

---

### 2.4 Choix des modèles et dataset (planification)

**Modèles choisis (en cours de planification pour implémentation) :**

| Composant | Choix | Usage prévu |
|-----------|-------|-------------|
| LLM | OmniRoute (OpenAI-compatible) `http://localhost:20128/v1`, modèle `kiro` | Enrichissement diagnostic, explications techniques |
| Embedding texte | BGE-M3 | Indexation des manuels constructeurs dans Qdrant |
| Embedding multimodal | CLIP | Indexation des images de voyants et pièces d'usure |
| Vector DB | Qdrant | Recherche vectorielle + BM25 + RRF |

**Dataset planifié :**

| Type | Contenu | Source prévue |
|------|---------|---------------|
| Manuels constructeurs | PDF (Bosch, Renault, Peugeot, etc.) | Extraction PyMuPDF |
| Images | Voyants de tableau de bord (MIL, ABS, Batterie, TPMS, AdBlue, Surchauffe) | Dataset à constituer |
| Images | Pièces d'usure (plaquettes de frein, disques, étriers) | Dataset à constituer |
| Données véhicules | VIN, marque, modèle, année, kilométrage, historique | Base synthétique MCP |
| Prix pièces Maroc | Cache JSON des sites Autops.ma et Cartec.ma | `data/pricing/prices_cache.json` (à enrichir lors du scraping) |

---

### 2.5 Serveur MCP (conception)

Le serveur MCP (Model Context Protocol) a été conçu pour exposer les outils de consultation et création de devis :

| Outil MCP | Description | Contrôle d'accès |
|-----------|-------------|------------------|
| `get_all_vehicles()` | Liste du parc avec spécifications | Tous les rôles authentifiés |
| `get_vehicle_spec(vin)` | Fiche technique détaillée d'un véhicule | Tous les rôles authentifiés |
| `get_vehicle_history(vin, user_role)` | Historique des interventions | Selon rôle utilisateur |
| `get_open_claims(vin, user_role)` | Sinistres/réclamations ouvertes | Selon rôle utilisateur |
| `create_repair_estimate(...)` | Création de devis officiel après approbation humaine | `expert_valideur`, `admin`, `technicien` |

Base de données MCP conçue : `data/synthetic/mcp_database.json`

---

### 2.6 Workflow Agentique LangGraph (conception)

Le workflow a été conçu avec les nœuds suivants (`src/agent/graph.py` et `src/agent/nodes.py`) :

| Nœud | Rôle conçu |
|------|------------|
| `verify_access` | Vérification injection de prompt + contrôles d'accès |
| `analyze_image_and_query` | Analyse multimodale (image + texte) |
| `retrieve_sources` | Recherche RAG (Qdrant + BM25 + RRF) |
| `rerank_sources` | Reclassement des chunks pertinents |
| `consult_mcp_history` | Consultation historique véhicule via MCP |
| `synthesize_and_verify` | Synthèse du diagnostic, préparation du devis (draft_action) |
| `fetch_part_prices` | Récupération prix pièces (cache + scraper) |
| `execute_mcp_action` | Création du devis final après approbation humaine |

---

## 3. LIVRABLES ATTENDUS POUR LA SEMAINE 2

| Livrable | Chemin | Description |
|----------|--------|-------------|
| Dossier d'architecture | Ce document (compte_rendu_semaine_2.md) | Conception détaillée des couches et flux |
| Diagrammes UML / Séquence | *À produire en supports de soutenance* | Séquence du workflow LangGraph, diagramme de classe Pydantic, diagramme de séquence MCP |
| Schéma des données Qdrant | `src/schemas/pydantic_models.py` | Modèles `Citation`, `AutoClaimOutput`, `PartPriceInfo` |
| Schéma JSON (Cache/MCP) | `data/pricing/prices_cache.json`, `data/synthetic/mcp_database.json` | Structure cache prix et base véhicules/devis (à finaliser) |

---

## 4. DÉFIS ANTICIPÉS POUR LA RÉALISATION (SEMAINE 3)

Les défis suivants ont été identifiés lors de la conception et devront être relevés lors de la phase de réalisation :

| Défi | Description | Action prévue |
|------|-------------|---------------|
| Mise en place environnement | Initialisation Git, configuration Docker Compose | Création `docker-compose.yml`, commits initiaux |
| Extraction des PDF | Lecture des manuels constructeurs avec PyMuPDF | Implémentation `src/ingestion/pdf_extractor.py` |
| Indexation vectorielle | Indexation BGE-M3 et CLIP dans Qdrant | Configuration collections Qdrant, pipeline d'indexation |
| API FastAPI | Développement API REST avec authentification JWT et RBAC | Routes `/auth/login`, `/diagnostic`, `/vehicles`, `/estimates` |

---

## 5. PLAN SEMAINE 3 (RÉALISATION)

### Objectifs & Tâches à Réaliser

- Mise en place de l'environnement : Git, Docker Compose
- Extraction des PDF : PyMuPDF (manuels constructeurs)
- Indexation vectorielle : BGE-M3 et CLIP dans Qdrant
- API FastAPI : authentification JWT, contrôle d'accès RBAC

### Livrable Attendu / Produit

- Repository Git initialisé
- Pipeline d'indexation fonctionnel
- API de base opérationnelle

---

## 6. CONCLUSION

La semaine 2 a permis de **concevoir et planifier** l'architecture complète du projet AutoDiag : workflow agentique LangGraph, RAG avec Qdrant, serveur MCP, modèles Pydantic stricts, RBAC à 4 rôles, et module pricing. Cette phase de conception constitue la base sur laquelle la **réalisation technique** s'appuiera à partir de la semaine 3 (mise en place de l'environnement, extraction des PDF, indexation vectorielle, et développement de l'API FastAPI).

---
*Fin du compte rendu de la semaine 2 — Phase de conception*