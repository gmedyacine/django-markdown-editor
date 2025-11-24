📄 Compte-rendu de réunion – Synchronisation Mail Triaging ↔ Domino Data Lab

Date : (à compléter)
Participants :

TAS : Thierry, Nivaldo

Domino Data Lab : Yacine (Tech Lead), Mickael (Scrum Master)

🎯 Rappel du besoin

L’application Mail Triaging doit permettre le téléchargement de fichiers contenant potentiellement des données sensibles.
L’objectif est de modifier le fonctionnement actuel, afin que les utilisateurs ne téléchargent plus directement les fichiers sur leurs postes, afin d’éviter toute fuite ou manipulation locale.

Aujourd’hui :

Le fichier est poussé vers COS, puis téléchargé par l’utilisateur.

Ce mécanisme doit évoluer pour garantir une gestion sécurisée (dataset Domino, droits, audit, etc.).

🧩 Solution initialement proposée par Domino Data Lab

Domino avait proposé la solution suivante :

Mail Triaging appelle une API produit Domino.

Cette API reçoit les infos nécessaires (UID, nom du fichier, use case…).

L’API déclenche un job Domino.

Le job récupère le fichier dans le bucket COS et le télécharge automatiquement dans le dataset Domino du bon projet.

❌ Pourquoi cette solution n’a pas été retenue ?

Nivaldo indique que l’intégration de cette API dans Mail Triaging demande des développements côté TAS.

L’équipe TAS n’a pas de bande passante disponible pour intégrer cette logique maintenant.

Le schéma augmente la charge côté Mail Triaging, ce qui n’est pas souhaitable dans l’immédiat.

💡 Solution privilégiée par l’équipe TAS

Nivaldo propose une solution plus simple côté TAS, mais moins user-friendly :

👉 Nouveau fonctionnement

L’utilisateur voit dans Mail Triaging le nom du fichier à récupérer.

Il se rend sur Domino.

Il saisit ce nom de fichier dans une WebApp dédiée.

Il clique sur Télécharger.

Domino va chercher le fichier directement dans le bucket COS et le place dans le dataset correspondant.

✔ Avantages

Aucun développement côté Mail Triaging

Charge de travail basculée vers Domino

Compatible avec l’organisation actuelle de TAS

❌ Limites

La solution est moins ergonomique (processus en deux étapes pour l’utilisateur)

Nécessite développement d’une WebApp Domino

Nécessite une gouvernance claire sur les datasets et les accès

Thierry et Nivaldo reconnaissent que cette solution n’est pas idéale, mais elle est actuellement la seule réalisable compte tenu des contraintes de charge de l’équipe TAS.

📌 Éléments extraits des notes de Mickael (photo)

Domino doit fournir une API permettant de déclencher la récupération depuis COS
(peut être réutilisée dans la WebApp Domino).

L’action utilisateur dans Mail Triaging doit simplement déclencher l'affichage du nom du fichier (pas d'appel API).

Une feature DOMINO : développer un dataset Domino connecté directement à COS (accès direct).

Un mapping UseCase ↔ Bucket doit être fourni par TAS.

⚠️ Cette information est indispensable pour router la récupération du fichier vers le bon emplacement.

L’ouverture des flux réseau Datalab ↔ Mail Triaging est à valider.

Fournir le Swagger/Postman de l'API Domino (côté Datalab).

Fournir un mécanisme d’accès aux HMAC/secrets (certificat ou token) pour sécuriser la récupération depuis COS.

📋 Plan d’action – To Do
Côté Datalab / Domino

Développer la WebApp Domino permettant la saisie du nom du fichier et le déclenchement du téléchargement.

Implémenter la logique de récupération depuis COS vers dataset.

Fournir la documentation API (Swagger / Postman).

Gérer les mécanismes d’authentification :

certificat ou clé HMAC

accès sécurisé au bucket

Côté TAS (Mail Triaging)

Fournir le fichier de mapping UseCase ↔ Bucket COS.

Afficher le nom du fichier côté Mail Triaging.

Aucun appel API à intégrer pour le moment.

🎯 Conclusion

Deux solutions ont été étudiées. La solution initiale, orientée API, a été écartée à cause du manque de bande passante côté TAS.
L’équipe valide une solution transitoire, plus simple à implémenter, où la charge bascule temporairement vers Domino Data Lab.

Cette approche permet de débloquer le projet rapidement, en attendant une future intégration complète avec Mail Triaging lorsque l’équipe TAS aura du temps.
