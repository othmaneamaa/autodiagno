# 📋 Livrable 5 : Fiche de Limites et Conditions d'Utilisation

**Application :** AutoClaim v1.0  
**Statut :** Prototype d'Aide à la Décision Technique  

---

## 1. Usages Autorisés

AutoClaim est strictement conçu pour :
- La recherche sémantique accélérée dans les manuels techniques d'atelier et guides constructeurs approuvés.
- L'assistance au diagnostic visuel préliminaire des voyants de tableau de bord et composants mécaniques (plaquettes, disques de freins).
- La consultation automatisée de l'historique d'entretien enregistré sous le format MCP.
- La préparation assistée de brouillons de devis d'intervention soumis à relecture et validation humaine obligatoire.

---

## 2. Usages Interdits et Hors Périmètre

Le système ne doit sous aucun prétexte être utilisé pour :
- **Le pilotage direct ou la commande d'organes du véhicule** (ex. effacement direct des codes défauts du calculateur ou reprogrammation de cartographie moteur sans intervention humaine qualifiée).
- **Le remplacement d'un technicien habilité** : toute manipulation sur circuit haute tension 400V exige des habilitations B2VL/BCL et le respect des protocoles physiques de sécurité.
- **La validation financière automatique** : aucun paiement, remboursement d'assurance ou commande de pièces ne peut être exécuté sans validation explicite par un expert habilité (*Human-in-the-Loop*).
- **L'utilisation comme diagnostic juridique opposable** : l'assistant constitue une aide documentaire non contractuelle.

---

## 3. Équipements Couverts par le Prototype

Le corpus documentaire du prototype couvre exclusivement :
1. **Famille Freinage et Liaisons au Sol :**
   - Étrier et disques ventilés avant (Tolérances et cotes minimales d'usure).
   - Plaquettes de freins organiques et céramiques.
   - Circuit hydraulique DOT4 et témoin d'anomalie répartiteur.
2. **Famille Groupe Motopropulseur et Électronique :**
   - Motorisations thermiques (Témoin MIL d'autodiagnostic injection/dépollution).
   - Motorisations diesel BlueHDi (Témoin d'alerte AdBlue/UREA et cycle FAP).
   - Boîtier servitude moteur (BSM) et cartographie des fusibles.
   - Procédures de consignation électrique haute tension.

*Tout équipement en dehors de ces périmètres fera l'objet d'un message d'incertitude et d'une demande de documentation complémentaire.*

---

## 4. Conditions et Précautions d'Utilisation

- **Qualité photographique :** Les photographies soumises doivent présenter une mise au point nette, un éclairage suffisant et cadrer clairement la zone suspecte. En cas de flou ou d'angle insuffisant, le système déclenche obligatoirement le statut `needs_clarification`.
- **Vérification systématique des citations :** L'utilisateur doit vérifier le numéro de page et le schéma cité avant d'engager toute action de démontage sur le véhicule.
- **Idempotence des devis :** Tout devis validé génère un identifiant unique et ne peut être soumis à nouveau sans modification explicite.
