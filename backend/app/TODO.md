# TODO — core (main, users, auth, database, settings)

Points restants de la revue du 2026-11-07. Hors périmètre : `core/organization.py`, `modules/`.

## 🔴 Bloquant

- [x] **`create_admin` plante sur une base neuve** — [core/users.py:51](core/users.py#L51)
      `settings.ADMIN_PASSWORD` est un `SecretStr`, passé tel quel à `hash_password` → pwdlib lève
      `TypeError: password must be str or bytes`. Ça ne se voit pas tant que l'admin existe déjà
      en base, ni dans les tests (le conftest crée l'admin lui-même).
      → `settings.ADMIN_PASSWORD.get_secret_value()`. Ajouter un test qui appelle `create_admin()`.

## 🟠 À faire

- [x] **Configuration (`Settings`)**
  - [x] Instanciée deux fois à l'import (`users.py:9`, `auth.py:18`). Centraliser : une instance
        unique ou `get_settings()` avec `@lru_cache` dans `core/settings.py`.
  - [x] Les tests dépendent de la présence de `.env.dev` à la racine du dépôt → plantage à la
        collecte en CI / sur une autre machine. Fournir des valeurs de test dans `conftest.py`
        (variables d'environnement posées avant l'import de `app.main`).
  - [x] `env_file=".env.dev"` + `env_file_depth=3` est résolu depuis le **répertoire courant**,
        pas depuis le fichier. Prévoir la config prod (variables d'env réelles, nom de fichier
        paramétrable, chemin absolu).

- [x] **Doublon de username : race condition** — [core/users.py:96-105](core/users.py#L96-L105)
      Le pré-check puis l'insert ne sont pas atomiques : deux POST simultanés → `IntegrityError`
      → 500. Attraper `IntegrityError` autour du `commit` (+ `session.rollback()`) et renvoyer 409.

- [x] **`int(token.sub)` peut lever `ValueError` → 500** — [core/auth.py:92](core/auth.py#L92)
      Typer `sub: int` dans `TokenPayload` (Pydantic convertit `"2"`, rejette `"admin"` → 401).
      Encoder avec `payload.model_dump(mode="json")` / `str(...)` pour garder un `sub` string (RFC 7519). >= laissé tel quel, doit être str dans je jwt

- [x] **Protection du router `users` portée par `main.py`** — [main.py:31](main.py#L31)
      Documenté par un commentaire, mais un oubli ailleurs exposerait `/users`. Sortir
      `require_admin` / `get_current_user` (ou les modèles) dans un module sans dépendance vers
      `users` pour casser le cycle, puis déclarer
      `APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])`.

- [ ] **Base de données** — [core/database.py](core/database.py)
  - [ ] Passage à PostgreSQL (TODO existant), URL lue depuis `Settings`.
  - [ ] Migrations avec Alembic : `create_all` ne modifie jamais une table existante.

## 🟡 Mineur

- [ ] Longueur des mots de passe incohérente : `min_length=4` pour `UserCreate` / `UserUpdate`,
      `5` pour `ADMIN_PASSWORD`. Recommandation : ≥ 8 (idéalement 12).
- [-] `create_admin` ne signale rien si un utilisateur non-admin s'appelle déjà `admin`
  (aucun admin créé). Au minimum un warning. => Le cas ne peut pas se produire, on ne peut pas supprimer l'utilisateur admin ni changer ses droits donc il n'y aura jamais un non-admin qui s'appelle admin
- [-] Déclarer `pydantic-settings` dans `pyproject.toml` (importé directement, aujourd'hui
  présent seulement via `fastapi[standard]`). pas nécessaire
- [ ] `conftest.py` : `TestClient(app)` sans `with` → le lifespan ne tourne pas (voulu). Si un
      jour on utilise `with TestClient(app)`, `create_db_and_tables()` / `create_admin()`
      toucheront la vraie `database.db`. Commenter, ou rendre ces fonctions injectables.

## 🧪 Tests (reporté)

- [ ] Découper `test_users` en tests indépendants (fixture `admin_headers`, plus d'ids en dur).
- [ ] Cas à couvrir :
  - [ ] token invalide / malformé / expiré (`decode_token`)
  - [ ] `/me` sans token
  - [ ] non-admin sur `POST` et `PATCH /users/...` → 403
  - [ ] username en doublon → 409
  - [ ] 422 : body incomplet, `user_id` non entier, mot de passe trop court
  - [ ] `create_admin()` sur base vide (cf. bug bloquant)
