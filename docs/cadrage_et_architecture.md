# 📑 Livrable 1 : Note de Cadrage et Architecture Technique

**Projet :** AutoClaim — Assistant Documentaire Multimodal et Agentique pour le Diagnostic Automobile  
**Référence :** Projet Intégrateur d'IA Générative Multimodale (Spécification MAINTIDOC)  

---

## 1. Cadrage du Projet

### 1.1 Objectifs Métier
AutoClaim est une aide à la décision destinée aux techniciens d'atelier et gestionnaires d'assurance automobile. Ses objectifs principaux sont :
- Réduire le temps de recherche dans les manuels constructeurs denses.
- Assister l'identification visuelle des témoins d'alerte et des pièces d'usure (freinage, moteur).
- Fournir des réponses techniques **100% vérifiables avec citations exactes** (nom du document, page, numéro de figure/schéma).
- Consulter l'historique d'interventions certifié via le protocole MCP (*Model Context Protocol*).
- Préparer des estimations de réparation sans jamais engager de dépenses de manière autonome : l'action sensible requiert obligatoirement une **approbation humaine explicite**.

### 1.2 Périmètre Opérationnel
- **Utilisateurs cibles :** Techniciens de maintenance, mécaniciens qualifiés, experts en sinistres, gestionnaires de flotte.
- **Entrées acceptées :** Questions en langage naturel (français), photographies de pièces ou de tableaux de bord (PNG, JPEG), numéros de série de véhicules (VIN à 17 caractères), documents PDF techniques.
- **Sorties générées :** Réponses structurées Pydantic, citations documentaires avec extraits, détection explicite d'incertitudes, questions de clarification, brouillons de devis d'intervention.
- **Hors périmètre :** Pilotage direct des véhicules ou des bancs d'essai électroniques, diagnostic médical ou légal garanti, validation autonome d'actions financières sans approbation humaine.

### 1.3 Deux Familles d'Équipements Couvertes
1. **Système de Freinage et Liaisons au Sol :** Plaquettes de frein (cotes minimales d'usure), disques de frein ventilés, étriers flottants, liquide de frein DOT4 et témoins d'anomalie du répartiteur REF.
2. **Groupe Motopropulseur et Électronique :** Voyant Autodiagnostic Moteur (MIL), voyant UREA/AdBlue (système SCR), boîtier servitude moteur (BSM / fusibles), consignation de sécurité haute tension 400V sur motorisations hybrides/électriques.

---

## 2. Architecture Technique et Flux de Données

### 2.1 Diagramme Général d'Architecture

```text
               +-------------------------------------------------------+
               |                  INTERFACE UTILISATEUR                |
               |                Streamlit (Port Web 8501)              |
               +---------------------------+---------------------------+
                                           | HTTP (JSON)
                                           v
               +-------------------------------------------------------+
               |                       API BACKEND                     |
               |                 FastAPI (Port Web 8000)               |
               |        Contrôle d'accès RBAC & Validation Token       |
               +---------------------------+---------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |               WORKFLOW AGENTIQUE LANGGRAPH            |
               |                                                       |
               |  1. verify_access (Sécurité & Détection Injection)   |
               |  2. analyze_image_and_query (VLM Qwen2.5-VL-7B)       |
               |  3. retrieve_sources (Recherche Hybride Qdrant)       |
               |  4. rerank_sources (Reranker Adapté MRR@10)          |
               |  5. consult_mcp_history (Client MCP)                  |
               |  6. synthesize_and_verify (Sortie Pydantic)           |
               |  7. execute_mcp_action (Human-in-the-Loop)            |
               +-------------+---------------------------+-------------+
                             |                           |
                             v                           v
              +---------------------------+ +--------------------------+
              |    MOTEUR RAG VECTORIEL   | |       SERVEUR MCP        |
              | - BGE-M3 & CLIP Embeddings| | - get_vehicle_history    |
              | - Reciprocal Rank Fusion  | | - get_open_claims        |
              | - Reranker fine-tuné      | | - create_repair_estimate |
              +---------------------------+ +--------------------------+
```

### 2.2 Flux de Traitement Détaillé
1. **Vérification d'accès :** Le nœud vérifie les permissions de l'utilisateur (RBAC) et soumet l'entrée textuelle et les métadonnées au module anti-injection de prompt.
2. **Analyse Multimodale :** Si une photo est fournie, le modèle vision-langage évalue sa lisibilité. Si l'image est floue ou ambiguë, le graphe bascule en interruption de clarification.
3. **Recherche & RRF :** Interrogation simultanée de la base vectorielle textuelle et visuelle, puis fusion des classements via *Reciprocal Rank Fusion*.
4. **Reclassement par Reranker :** Le modèle de reranking adapté réordonne les extraits pour maximiser la fidélité documentaire.
5. **Appel MCP :** Si un VIN est identifié, l'agent interroge l'historique et les sinistres ouverts sans dépasser le budget de 3 appels.
6. **Synthèse et Devis :** Construction d'une réponse validée par schéma Pydantic. Si une réparation est préconisée, un brouillon de devis chiffré est préparé avec un token unique `APP-XXXXXX`.
7. **Human-in-the-Loop :** L'action sensible reste en attente jusqu'à l'approbation explicite de l'utilisateur dans l'interface graphique.

---

## 3. Analyse des Risques et Stratégies d'Atténuation

| Risque Identifié | Impact | Probabilité | Mesure d'Atténuation Mise en Œuvre |
| :--- | :---: | :---: | :--- |
| **Hallucination technique du VLM** | Élevé | Moyenne | Obligation stricte de citations avec numéro de page et de figure ; abstention explicite en cas de doute. |
| **Attaque par injection de prompt** (ex. faux ordres dans les OCR) | Élevé | Faible | Détection regex préventive, traitement des documents comme des données passives, tests d'injection dédiés. |
| **Création accidentelle de devis en double** | Moyen | Moyenne | Clé d'idempotence unique (`idempotency_key`) générée côté client et contrôlée par le serveur MCP. |
| **Dépassement de coûts d'inférence (Boucle infinie)** | Moyen | Faible | Budgets stricts codés en dur : maximum 3 appels MCP, 6 appels de modèle et timeout de 60 secondes. |
| **Fuite de données confidentielles d'atelier** | Élevé | Faible | Filtrage RBAC systématique en amont de la récupération vectorielle (les techniciens ne reçoivent aucun extrait admin). |
