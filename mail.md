# Open Questions — Artifactory / Domino DataLab Workshop

---

## 1. Comment Artifactory gère l'indexation ?

Artifactory expose automatiquement un index PyPI compatible (`/simple/`) pour chaque repo configuré.

Le `pip.conf` embarqué dans le Dockerfile pointe vers cet index :

```ini
[global]
index-url = https://<user>:<token>@artifactory.bnpparibas.com/artifactory/api/pypi/pypi-proxy/simple
extra-index-url = https://<user>:<token>@artifactory.bnpparibas.com/artifactory/api/pypi/pypi-local/simple
```

Quand Domino exécute le `docker build` et lance `pip install -r requirements.txt`, pip interroge cet index exactement comme il interrogerait PyPI — de façon transparente pour le Data Scientist.

**Aucune configuration manuelle n'est nécessaire côté DS.** L'indexation est gérée automatiquement par Artifactory.

---

## 2. Comment est gérée l'authentification auprès d'Artifactory pour les readers ?

### Contrainte importante confirmée par la doc Domino

> **Docker ne peut pas accéder aux user/project environment variables au moment du `docker build`.**
> Ces variables ne sont injectées qu'au runtime (workspace, job) — pas pendant le build d'environnement.

### Solution recommandée — Compute Environment Variables (stockées dans Domino)

Les credentials Artifactory doivent être stockés directement dans la définition de l'environnement Domino :

**Étapes :**
1. Aller dans `Govern → Environments → [ton env] → Edit Definition`
2. Descendre jusqu'à la section **"Environment variables"**
3. Ajouter les deux variables :
   - `ARTIFACTORY_USERNAME` → valeur du tech user
   - `ARTIFACTORY_TOKEN` → token Artifactory
4. Dans le champ **"Dockerfile Instructions"**, déclarer les ARG :

```dockerfile
ARG ARTIFACTORY_USERNAME
ARG ARTIFACTORY_TOKEN
RUN pip config set global.index-url \
    https://${ARTIFACTORY_USERNAME}:${ARTIFACTORY_TOKEN}@artifactory.bnpparibas.com/artifactory/api/pypi/pypi-proxy/simple
```

**Avantages de cette approche :**
- Les credentials sont stockés **une seule fois** dans Domino, chiffrés
- GitLab CI déclenche le build via l'API Domino **sans passer les credentials**
- Domino les récupère lui-même depuis sa config d'environnement au moment du build
- Le token ne transite **jamais en clair** dans les logs GitLab CI

### Alternative moins sécurisée (à éviter si possible)

GitLab CI passe les credentials via l'API Domino au moment du trigger de build :

```yaml
# .gitlab-ci.yml
build_domino_env:
  script:
    - curl -X POST $DOMINO_API/environments/$ENV_ID/builds
        -H "X-Domino-Api-Key: $DOMINO_API_KEY"
        --data '{"buildArguments": {"ARTIFACTORY_TOKEN": "$ARTIFACTORY_TOKEN"}}'
```

⚠️ **Risque** : le token transite dans l'appel API et peut apparaître dans les logs CI.

### Droits d'accès

| Repo Artifactory | Accès lecture |
|---|---|
| Proxy PyPI | Tous les DS (token commun) |
| Standalone repo privé | DS habilités au projet = même périmètre GitLab |
| Repo binaires | Build Domino uniquement |

---

## 3. Comment est gérée la reproductibilité avec une installation au runtime ?

**Rien n'est installé au runtime.** C'est le principe fondamental de l'approche retenue.

### Cycle complet

| Étape | Ce qui se passe |
|---|---|
| DS modifie `requirements.txt` ou `Dockerfile` | Dans GitLab, sur une branche feature/ |
| Merge Request → merge master | CI lint + tests + peer review |
| GitLab CI appelle l'API Domino | Déclenche le build de l'environnement |
| Domino exécute le Dockerfile instructions | pip install résolu via Artifactory · credentials depuis Compute Env Variables |
| Env figé et versionné | `env-nlp-v3` · `env-ml-v4` · `env-cv-v2` |
| DS sélectionne l'env dans Domino | Workspace · Job training · Model API deploy |

### Garantie de reproductibilité

Le même environnement figé est utilisé à toutes les étapes :

| Étape | Environnement |
|---|---|
| Workspace DS | `env-ml-v4` |
| Job training | `env-ml-v4` (identique) |
| Model API deploy | `env-ml-v4` (identique) |

Le problème du *"ça marche chez moi mais pas en prod"* est éliminé.

---

## Note — Artifactory Standalone vs GitLab Package Registry

| | Artifactory Standalone | GitLab Package Registry |
|---|---|---|
| Mirror PyPI automatique | ✅ Oui | ❌ Non |
| Index `/simple/` compatible pip | ✅ Oui | ✅ Oui |
| Credentials stockés dans Domino Compute Env | ✅ Recommandé | Manuel |
| Packages publics disponibles | ✅ Via proxy PyPI | ❌ Push manuel uniquement |
| Credentials jamais en clair dans CI | ✅ Si Compute Env Variables | ⚠️ Risque si passés via API |
| **Recommandation** | ✅ **Cible** | ⚠️ Migration à planifier |
