Objet : Compte-rendu de réunion – Synchronisation Mail Triaging / Domino Data Lab

Bonjour Thierry, bonjour Nivaldo,

Suite à notre échange d’aujourd’hui avec Mickael et moi-même côté Datalab, voici un récapitulatif clair des décisions et orientations retenues concernant l’intégration Mail Triaging ↔ Domino.

🧩 1. Rappel du besoin

Le mécanisme actuel de téléchargement via Mail Triaging doit évoluer afin d’éviter que les utilisateurs téléchargent localement des fichiers contenant des données sensibles. L’objectif est de basculer ces téléchargements vers un dataset Domino sécurisé, intégrant audit, gouvernance et restrictions d’accès.

🔄 2. Solution initialement proposée par Datalab

La proposition initiale côté Domino consistait à :

Appeler une API Domino depuis Mail Triaging.

L’API recevait les informations nécessaires (UID, nom du fichier, contexte métier…).

Elle déclenchait un job Domino chargé de récupérer automatiquement le fichier depuis COS et de l’insérer dans le dataset du projet concerné.

❌ Blocage

Cette solution demande du développement côté TAS, et l’équipe n’a pas de bande passante actuellement pour intégrer et maintenir cette API.

⭐ 3. Solution retenue par TAS (solution transitoire)

Une solution plus simple, centrée côté Domino, a été validée.

Principe fonctionnel :

Mail Triaging affiche le nom du fichier à récupérer.

L’utilisateur se rend sur Domino.

Une WebApp Domino permet de saisir ce nom.

Domino récupère le fichier depuis le bucket COS associé au UseCase.

Le fichier est déposé dans le dataset Domino du projet.

Observations :

Solution moins user-friendly, reconnue par Thierry et Nivaldo.

Mais réalisable immédiatement, sans impact côté Mail Triaging.

📌 4. Prérequis identifiés
Côté TAS

Fournir le mapping UseCase → Bucket COS, indispensable au routage automatique.

Côté Datalab

Développer la WebApp Domino permettant la récupération manuelle.

Exposer le Swagger/Postman de l’API interne Domino.

Gérer l’accès sécurisé au bucket (HMAC / certificat).

Valider les flux réseau Domino ↔ COS ↔ Mail Triaging.

📋 5. Actions
Action	Responsable	Commentaire
Fournir le mapping UseCase → Bucket COS	TAS	Bloquant pour démarrer les développements
Développer la WebApp Domino	Datalab	Saisie du nom + récupération sécurisée
Exposer l’API interne (Swagger/Postman)	Datalab	Prérequis pour une future intégration TAS
Mise en place accès HMAC / certificat	Datalab	Nécessaire pour sécuriser le flux COS
Validation des flux réseau	Infra / Datalab	COS / Domino / Mail Triaging
🏁 6. Conclusion

La solution API complète est mise en pause faute de disponibilité TAS.
Nous avançons avec une solution transitoire, intégralement portée par Domino, permettant de débloquer le projet rapidement tout en respectant les exigences de sécurité.

N’hésitez pas à revenir vers nous si un ajustement est nécessaire.

Bien cordialement,
