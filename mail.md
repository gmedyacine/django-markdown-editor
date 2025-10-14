**Objet :** Escalade – Problème critique de *shared memory* sur les Hardware Tiers Domino

Bonjour [Prénom du responsable ITG],

Je souhaite vous alerter sur un **problème critique lié à la configuration de la shared memory** sur les Hardware Tiers de la plateforme **Domino Datalab**  
(`dmn-ap87993-prod-1d595faf.datalab.cloud.echonet`).

---

### 🔎 Contexte
Depuis plusieurs jours, plusieurs équipes rencontrent des **échecs récurrents de jobs** sur Domino, en particulier sur des workloads PyTorch et deep learning.  
Après analyse, la cause principale est la **limite de shared memory fixée à 64 Mo** sur les Hardware Tiers (`wks-cpu-xxx`, `wks-gpu-xxx`).

Cette valeur est **trop faible** et provoque des erreurs « out of shared memory », bloquant l’exécution des modèles.

Des échanges ont déjà eu lieu sur ce sujet avec l’équipe ITG (voir la conversation ci-dessous) :  
👉 [Lien vers la conversation Teams / ITGP Domino Support CARDIF Datalab](COLLE_ICI_LE_LIEN)

---

### ⚙️ Actions déjà menées
- Plusieurs tests ont été réalisés sur différents Hardware Tiers (`wks-cpu-4x16`, `wks-gpu-7x96-h100-1x340`).  
- Une proposition a été faite par ITG pour augmenter la *shared memory* à **50 % de la RAM du tier**.  
- Un premier test a été réalisé avec une valeur de **192 GiB sur un GPU tier**, confirmant l’amélioration.  
- Cependant, la configuration par défaut **reste à 64 Mo** sur la majorité des tiers, ce qui **bloque encore les jobs utilisateurs**.

---

### 🚨 Impact
- Les Data Scientists ne peuvent pas exécuter leurs modèles ni valider leurs entraînements.  
- Les jobs Domino échouent systématiquement sur certains tiers.  
- Le risque de blocage sur les environnements de préproduction et production est élevé.

---

### ✅ Attente
Nous demandons une **mise à jour urgente** de la configuration *shared memory* sur les Hardware Tiers Domino :  
- soit **50 % de la RAM totale**,  
- soit **au moins 192 GiB sur les GPU tiers**.  

Nous restons disponibles pour accompagner les tests et valider la configuration après mise à jour.

---

Je vous remercie par avance pour votre réactivité sur ce point critique,  
et reste à disposition pour tout complément d’information.

Bien cordialement,  
**Mohamed Yassine GHARSALLAOUI**  
DevOps / Domino Datalab – CARDIF  

*(En copie : [Nom de ton manager])*  
