# POINT — Problèmes et difficultés rencontrés (Semaine 2)

## Projet AutoDiag (anciennement AutoClaim) — Phase de conception

**Étudiant :** Othmane Amaadour  
**Date :** 12 novembre 2026  
**Path du projet :** `C:\Users\Lenovo\Desktop\pfa-project-mix`

---

## 1. CONTEXTE DE LA SEMAINE 2

La semaine 2 a été consacrée à la **conception architecturale et à la planification** du projet AutoDiag : définition de l'architecture modulaire, des modèles Pydantic, des rôles RBAC, du choix des modèles LLM/dataset, et du schéma des données (Qdrant + JSON). Aucun développement fonctionnel complet n'a encore été réalisé à ce stade ; c'est une phase de spécification.

---

## 2. PROBLÈMES ET DIFFICULTÉS RENCONTRÉS (SEMAINE 2)

### 2.1 Sélection du véhicule incorrecte dans l'interface

**Problème :** L'interface Streamlit affichait systématiquement une **Peugeot 208 1.2 PureTech** (VIN : VF3CC8HR0ES123456) comme véhicule par défaut, indépendamment du véhicule saisi dans la question technique (ex: Renault Clio 4 1.5 dCi 2018).

**Cause :** Le sélecteur de véhicule dans `src/ui/app.py` utilisait un index fixe (`index=0`) qui pointait sur le premier véhicule de la liste, sans lien avec la question de l'utilisateur.

**Impact :** Tous les diagnostics, devis et prix étaient générés pour le mauvais véhicule.

**Statut :** Identifié en conception — correction prévue en semaine 3 (ajout du véhicule Clio 4 dans la base MCP et modification de la logique de sélection).

---

### 2.2 Coûts des devis en € au lieu de MAD

**Problème :** Les coûts estimés (`estimated_cost`) des actions proposées (draft_action) étaient codés en **euros** (ex: 185.00 €) dans les nœuds LangGraph.

**Cause :** Le projet est marocain et doit afficher les prix en **dirhams marocains (MAD)**, mais les valeurs avaient été définies en euros lors de la conception.

**Impact :** Incohérence avec le marché cible (Maroc) et les prix pièces en MAD.

**Statut :** Identifié en conception — conversion vers MAD prévue en semaine 3.

---

### 2.3 "Total estimé des pièces" incorrect (doublons inter-vendeurs)

**Problème :** L'onglet 💰 Prix Pièces additionnait les prix de produits similaires provenant de deux vendeurs différents (ex: plaquettes Bosch sur Autops + plaquettes Textar sur Cartec) et affichait un total sans signification commerciale.

**Cause :** La fonction de calcul de coût total sommait tous les prix sans distinguer le site/vendor.

**Impact :** Affichage d'un total erroné qui induisait en erreur l'utilisateur.

**Statut :** Identifié en conception — suppression de l'affichage du total prévue, garde uniquement le groupement par site.

---

### 2.4 Cache pricing identique pour tous les problèmes d'une même famille

**Problème :** Tous les problèmes de freinage (plaquettes, bruit, ABS, disques, étrier) renvoyaient les mêmes 3 produits, quelle que soit la question précise.

**Cause :** La clé de cache ne correspondait qu'à la `equipment_family` (ex: `systeme_freinage_liaisons_au_sol`) sans tenir compte du mot-clé pièce spécifique (plaquettes, disques, etc.) ni du véhicule.

**Impact :** Manque de spécificité des prix affichés par type de pièce.

**Statut :** Identifié en conception — enrichissement du cache JSON avec des clés par pièce et véhicule prévu en semaine 3.

---

### 2.5 Véhicule Clio 4 absent de la base MCP

**Problème :** La base de données véhicules (`data/synthetic/mcp_database.json`) ne contenait aucun modèle Renault Clio 4, rendant impossible sa sélection pour les tests.

**Cause :** La base véhicules synthétiques n'incluait pas ce modèle courant au Maroc.

**Impact :** Impossible de tester le scénario "Clio 4 bruit métallique freinage" conçu pour la semaine 2.

**Statut :** Identifié en conception — ajout du véhicule Clio 4 (VIN : VF1RZJ00H56123456) prévu en semaine 3.

---

### 2.6 Module bs4 (BeautifulSoup4) non installé

**Problème :** L'application Streamlit refusait de démarrer avec l'erreur :

```
ModuleNotFoundError: No module named 'bs4'
```

**Cause :** La dépendance `beautifulsoup4` n'était pas installée dans l'environnement Python utilisé, bien que `src/pricing/scraper.py` l'importe.

**Impact :** Blocage du lancement de l'interface.

**Statut :** Résolu — installation via `pip install beautifulsoup4`.

---

### 2.7 `st.set_page_config()` pas en premier dans Streamlit

**Problème :** L'application plantait avec l'erreur :

```
StreamlitSetPageConfigMustBeFirstCommandError: set_page_config() can only be called once per app page, and must be called as the first Streamlit command in your script.
```

**Cause :** `st.markdown("<style>...")` était appelé avant `st.set_page_config()` dans `src/ui/app.py`.

**Impact :** L'interface ne pouvait pas démarrer.

**Statut :** Résolu — déplacement de `st.set_page_config()` en tête de fichier.

---

### 2.8 Vrai scraping Autops.ma / Cartec.ma impossible (protection anti-bot)

**Problème :** Le module `PricingScraper` (basé sur `requests` + `BeautifulSoup`) ne peut pas scraper les vrais sites Autops.ma et Cartec.ma.

**Causes :**

- Protection **Cloudflare / WAF** bloquant les requêtes HTTP simples sans exécution JavaScript.
- Sites **dynamiques (SPA)** : contenu produits injecté par JavaScript, invisible pour BeautifulSoup.
- Sélecteurs CSS instables.

**Impact :** Impossibilité de récupérer des prix réels en temps réel pour la démo.

**Solution retenue (conception semaine 2) :** Utilisation d'un **cache simulé enrichi** (`data/pricing/prices_cache.json`) au lieu du scraping réel. Migration vers Playwright prévue pour une version production.

---

## 3. RÉSUMÉ DES FICHIERS CONCERNÉS

| Fichier | Problème(s) identifié(s) en semaine 2 |
|---------|--------------------------------------|
| `src/ui/app.py` | Véhicule par défaut, set_page_config, suppression total pièces |
| `src/agent/nodes.py` | Coûts en € au lieu de MAD |
| `src/pricing/service.py` | Clé de cache trop générique (famille seulement) |
| `src/pricing/prices_cache.json` | Cache trop limité (2 clés seulement) |
| `data/synthetic/mcp_database.json` | Véhicule Clio 4 absent |
| `requirements.txt` | Dépendance beautifulsoup4 manquante |

---

*Fin du point — Problèmes et difficultés semaine 2 (conception)*