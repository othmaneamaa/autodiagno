# COMPTE RENDU — SEMAINE 3
## Projet AutoDiag (anciennement AutoClaim) — Assistant Multimodal et Agentique Automobile

**Étudiant :** Othmane Amaadour  
**Date :** Novembre 2026  
**Path du projet :** `C:\Users\Lenovo\Desktop\pfa-project-mix\`

---

## 1. OBJECTIFS DE LA SEMAINE 3

Les objectifs fixés pour la semaine 3 étaient :

| # | Objectif | Détail | Statut |
|---|----------|--------|--------|
| 1 | Mise en place de l'environnement | Git (initialisation, commits), Docker Compose (orchestration services) | ✅ Git initialisé |
| 2 | Extraction des PDF | PyMuPDF pour l'extraction de texte des manuels constructeurs PDF | 🔄 En cours |
| 3 | Indexation vectorielle | BGE-M3 (texte) et CLIP (images) dans Qdrant | 🔄 En cours |
| 4 | API FastAPI | API REST avec authentification JWT et contrôle d'accès RBAC | 🔄 En cours |
| 5 | Livrable attendu | Repository Git initialisé, pipeline d'indexation fonctionnel, API de base opérationnelle | 🔄 En cours |

---

## 2. TÂCHES RÉALISÉES

### 2.1 Mise en place de l'environnement (Git, Docker Compose)

**Git :**
- Dépôt Git initialisé sur `main`
- Commits effectués sur les fonctionnalités développées (premier commit : `7574258`)
- Fichiers suivis et modifiés : `requirements.txt`, `src/agent/graph.py`, `src/agent/nodes.py`, `src/schemas/pydantic_models.py`, `src/ui/app.py`
- Nouveaux dossiers suivis : `data/pricing/`, `src/pricing/`

**Docker Compose :**
- À configurer pour l'orchestration des services (Qdrant, API FastAPI, Interface Streamlit, LLM OmniRoute)
- Fichier `docker-compose.yml` à créer à la racine du projet

---

### 2.2 Extraction des PDF (PyMuPDF)

**Objectif :** Extraire le texte et les métadonnées des manuels constructeurs PDF (Bosch, Renault, Peugeot, etc.) pour alimenter la base de connaissances RAG.

**Outil :** PyMuPDF (`fitz`) — extraction de texte, tableaux, et métadonnées des documents PDF techniques.

**Statut :** Pipeline d'extraction à implémenter dans `src/ingestion/pdf_extractor.py` (ou similaire). Les PDF sources sont attendus dans un dossier `data/pdfs/` ou `data/manuals/`.

---

### 2.3 Indexation vectorielle (BGE-M3 + CLIP dans Qdrant)

**Objectif :** Indexer le contenu extrait dans Qdrant pour la recherche sémantique hybride (texte + image).

| Modèle | Type | Usage |
|--------|------|-------|
| **BGE-M3** | Embedding texte | Indexation des extraits de manuels PDF (procédures, couples de serrage, références OEM) |
| **CLIP** | Embedding multimodal | Indexation des images de voyants et pièces d'usure (recherche texte ↔ image) |

**Vector DB :** Qdrant — stockage des vecteurs avec payload (métadonnées : document_id, page, element_id, catégorie de panne).

**Recherche hybride :**
- Recherche vectorielle (BGE-M3 pour le texte, CLIP pour l'image)
- BM25 (recherche lexicale)
- RRF (Reciprocal Rank Fusion) pour combiner les résultats

**Statut :** À implémenter dans `src/ingestion/vector_indexer.py` et `src/reranker/reranker_service.py`.

---

### 2.4 API FastAPI avec authentification JWT / RBAC

**Objectif :** Exposer une API REST pour le diagnostic automobile avec sécurité d'accès.

**Endpoints prévus :**
| Endpoint | Méthode | Rôle requis | Description |
|----------|---------|-------------|-------------|
| `/auth/login` | POST | Public | Authentification, retour token JWT |
| `/auth/me` | GET | Authentifié | Profil utilisateur connecté |
| `/diagnostic` | POST | technicien, expert_valideur, admin | Lancer un diagnostic agentique |
| `/vehicles` | GET | tous | Liste des véhicules du parc |
| `/vehicles/{vin}/history` | GET | tous | Historique d'un véhicule (MCP) |
| `/estimates` | POST | expert_valideur, admin | Créer un devis (après approbation HITL) |
| `/estimates` | GET | gestionnaire_flotte, admin | Lister les devis |

**Sécurité :**
- **JWT** : Token d'accès émis après login, expiration configurée
- **RBAC** : 4 rôles — `technicien`, `expert_valideur`, `gestionnaire_flotte`, `admin`
- **Middleware** : Vérification du token sur les routes protégées

**Statut :** Authentification basique déjà présente dans `src/auth/auth_service.py` (Streamlit). Migration vers API FastAPI avec JWT en cours.

---

## 3. LIVRABLES ATTENDUS

| Livrable | Statut | Commentaire |
|----------|--------|-------------|
| Repository Git initialisé | ✅ | Dépôt sur branche `main`, historique des commits |
| Pipeline d'indexation fonctionnel | 🔄 | Extraction PDF + indexation Qdrant à finaliser |
| API de base opérationnelle | 🔄 | FastAPI + JWT/RBAC à implémenter |

---

## 4. ARCHITECTURE MISE EN PLACE (SEMAINE 3)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COUCHE API (FastAPI)                               │
│  /auth/login, /diagnostic, /vehicles, /estimates — JWT + RBAC              │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COUCHE ORCHESTRATION (LangGraph)                       │
│  Workflow agentique : verify → analyze → retrieve → rerank → synthesize     │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐   ┌───────────────────┐   ┌──────────────────────┐
│   RAG Qdrant  │   │   SERVEUR MCP     │   │   PRICING / SCRAPING │
│  BGE-M3 +     │   │  Véhicules,       │   │  Autops.ma, Cartec.ma│
│  CLIP + BM25  │   │  Historique,      │   │  Cache JSON          │
│  + RRF        │   │  Devis            │   │                      │
└───────────────┘   └────────────────────┘   └─────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COUCHE DONNÉES (Docker Compose)                        │
│  Qdrant (vectoriel), PostgreSQL/MySQL (optionnel), Redis (cache JWT)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. DIFFICULTÉS RENCONTRÉES ET SOLUTIONS

| Difficulté | Solution prévue |
|------------|-----------------|
| Intégration PyMuPDF pour l'extraction PDF | Installation de `pymupdf` dans `requirements.txt` |
| Indexation BGE-M3 + CLIP dans Qdrant | Configuration des modèles d'embedding, création des collections Qdrant |
| Authentification JWT + RBAC sur FastAPI | Implémentation de middleware de vérification de token, décorateurs de rôles |
| Orchestration multi-services | Fichier `docker-compose.yml` pour Qdrant, API, UI, LLM |

---

## 6. PLAN SEMAINE 4 (PRÉVISION)

- [ ] Finaliser le pipeline d'indexation (PDF → BGE-M3/CLIP → Qdrant)
- [ ] Déployer l'API FastAPI avec JWT/RBAC opérationnelle
- [ ] Tester l'authentification et les contrôles d'accès par rôle
- [ ] Relier l'interface Streamlit à l'API FastAPI (au lieu d'appel direct aux fonctions)
- [ ] Tests complets bout-en-bout (diagnostic → devis → approbation HITL)

---

## 7. CONCLUSION

La semaine 3 est consacrée à la **mise en production technique** du projet : environnement conteneurisé (Docker Compose), pipeline d'indexation documentaire (PyMuPDF + BGE-M3 + CLIP + Qdrant), et exposition via une API sécurisée (FastAPI + JWT + RBAC). Le repository Git est déjà initialisé et versionne l'avancement du code. Les briques RAG et API seront pleinement opérationnelles en fin de semaine pour permettre le déploiement complet d'AutoDiag.

---
*Fin du compte rendu de la semaine 3*