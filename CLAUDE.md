# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack accounting and budgeting application with FastAPI backend, Vue 3 frontend, and PostgreSQL database. All services containerized with Docker Compose. Features include user authentication with optional 2FA, multi-currency account management, transaction tracking with category management, and budget planning.

## Development Commands

### Running the Application

```bash
# Start all services (recommended for development)
docker-compose up --build

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart [backend|frontend|db]

# View logs
docker-compose logs -f [backend|frontend|db]

# View last N lines of logs
docker-compose logs --tail 50 backend
```

**Access Points:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Database: localhost:5432 (user: accounting_user, db: accounting_db)

### Installing Dependencies in Running Containers

When adding new npm packages or Python dependencies, install them in the running container:

```bash
# Frontend - install npm package
docker-compose exec frontend npm install <package-name>
docker-compose restart frontend

# Backend - install Python package
docker-compose exec backend pip install <package-name>
# Update requirements.txt for persistence
```

### Backend Development

```bash
# Run backend locally (requires PostgreSQL running)
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
# Run frontend locally
cd frontend
npm install
npm run dev

# Build for production
npm run build
```

## Architecture Overview

### Backend Architecture (FastAPI + SQLAlchemy + PostgreSQL)

**Request Flow:**
1. Request → FastAPI app (`backend/app/main.py`)
2. CORS middleware validates origin
3. Router endpoint (`backend/app/api/`) receives request
4. Pydantic schema validates request body (`backend/app/schemas/`)
5. Dependency injection provides `get_current_user()` and `get_db()` session
6. Business logic interacts with SQLAlchemy models (`backend/app/models/`)
7. Response serialized via Pydantic response model

**Authentication Flow:**
- Standard login: OAuth2PasswordRequestForm (FormData) → JWT token
- 2FA enabled: Initial login returns `requires_2fa: true` → separate 2FA verification endpoint with TOTP code → final JWT token
- JWT created via `app.core.security.create_access_token()` with username in subject
- Token expires at 23:59:59 on day of creation (resets daily)
- Protected endpoints use `current_user: User = Depends(get_current_user)` from `app.api.deps`
- Frontend stores token in localStorage, axios interceptor attaches to requests

**2FA Implementation:**
- Uses pyotp library for TOTP (Time-based One-Time Password)
- User model has `two_factor_enabled` (Boolean) and `two_factor_secret` (String)
- Setup: `/api/users/me/2fa/setup` generates secret and QR code (base64 image)
- Verification: `/api/users/me/2fa/verify` with 6-digit code
- Login flow: `/api/auth/login` → `/api/auth/login/2fa/verify` (if 2FA enabled)
- Compatible with Google Authenticator, Microsoft Authenticator, etc.

**Database Relationships:**
- `User` → one-to-many → `Account` (via user_id)
- `User` → one-to-many → `Budget` (via user_id)
- `User` → one-to-many → `Category` (via user_id)
- `Account` → one-to-many → `Transaction` (via account_id)

**Critical Security Pattern:**
All API endpoints MUST filter by `current_user.id` to enforce user data isolation. Never expose other users' data.

```python
# Correct pattern
accounts = db.query(Account).filter(Account.user_id == current_user.id).all()

# Wrong - exposes all users' data!
accounts = db.query(Account).all()
```

**Password Validation:**
Enforced on backend via Pydantic validators in `schemas/user.py`:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (!@#$%^&*(),.?":{}|<>)

### Frontend Architecture (Vue 3 + Vite + Pinia)

**State Management:**
- Authentication state in Pinia store (`frontend/src/stores/auth.ts`)
- JWT token persisted in localStorage
- All other state is component-local (no global state for business data)

**API Communication:**
- Centralized in `frontend/src/services/api.ts`
- Axios interceptor automatically attaches Bearer token to all requests
- Axios interceptor handles 401 errors: clears token and redirects to /login (except for /auth/login and /auth/register requests)

**Special API Call Patterns:**
```typescript
// Standard login - uses FormData
login(credentials: UserLogin) {
  const formData = new FormData()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)
  return api.post<Token>('/auth/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 2FA verification - sends JSON with username, password, and token
verify2FA(credentials: UserLogin, token: string) {
  return api.post<Token>('/auth/login/2fa/verify', {
    username: credentials.username,
    password: credentials.password,
    token: token
  })
}
```

**Routing:**
- Protected routes use `meta: { requiresAuth: true }`
- Navigation guard in `frontend/src/router/index.ts` enforces authentication
- Guard prevents infinite redirects by checking `to.path === from.path`
- Authenticated users accessing /login or /register redirect to /

**Modal-Based Error Handling:**
Registration and login errors display in modals, not inline. Forms validate client-side before submission to prevent unnecessary API calls.

**Dashboard Quick Transaction Feature:**
Each account card has a "記帳" (record transaction) button that opens a pre-filled modal for that specific account. Uses datetime-local input for timestamp.

### Transaction Balance Logic

**Critical:** Transactions directly modify account balances:

```python
# Credit (income) - adds to balance
if transaction_type == 'credit':
    account.balance += amount

# Debit (expense) - subtracts from balance
if transaction_type == 'debit':
    account.balance -= amount
```

When updating/deleting transactions:
1. Reverse the old transaction's effect on balance
2. Apply the new transaction's effect (for updates)

See `backend/app/api/transactions.py` for implementation.

### Category Management System

**Backend:**
- Categories are user-specific (one-to-many from User)
- Each category has `order_index` for custom sorting
- First API call auto-creates default categories: 飲食、交通、購物、醫療、娛樂
- Endpoints: GET, POST, PUT, DELETE, POST /reorder (batch update)

**Frontend:**
- Categories loaded on Dashboard mount
- Transaction forms use `<select>` with categories
- Drag-and-drop reordering using Sortable.js library
- Management modal allows add/edit/delete/reorder
- Changes immediately sync to backend

## Database Schema

Tables auto-created on backend startup via `Base.metadata.create_all(bind=engine)` in main.py.

**Key Models:**

`User`:
- id, username, hashed_password
- two_factor_enabled, two_factor_secret
- created_at, updated_at

`Account`:
- id, name, account_type, balance, currency, description
- user_id (FK), created_at, updated_at
- Types: asset, liability, equity, revenue, expense

`Transaction`:
- id, description, amount, transaction_type, category, transaction_date
- account_id (FK), created_at, updated_at
- Types: credit (income), debit (expense)

`Budget`:
- id, name, category, amount, spent, period, start_date, end_date
- user_id (FK), account_id (FK), created_at, updated_at
- Periods: monthly, quarterly, yearly

`Category`:
- id, name, order_index
- user_id (FK), created_at, updated_at

## Common Development Workflows

### Adding New API Endpoints

1. Create Pydantic schemas in `backend/app/schemas/` (Base, Create, Update, Response)
2. Create/update SQLAlchemy model in `backend/app/models/`
3. Update `backend/app/models/__init__.py` to export new model
4. Create router in `backend/app/api/` with CRUD operations
5. Register router in `backend/app/main.py`: `app.include_router(...)`
6. Always use `current_user: User = Depends(get_current_user)` for protected endpoints
7. Filter all queries by `current_user.id`

### Adding New Frontend Views

1. Create component in `frontend/src/views/`
2. Add TypeScript types in `frontend/src/types/index.ts`
3. Add API methods in `frontend/src/services/api.ts`
4. Add route in `frontend/src/router/index.ts` with `meta: { requiresAuth: true }`
5. Add navigation link to `frontend/src/App.vue` navbar if needed

### Adding New Dependencies

**Frontend (npm packages):**
```bash
# Install in running container
docker-compose exec frontend npm install <package-name>

# Restart to rebuild
docker-compose restart frontend

# Or rebuild if needed
docker-compose up --build frontend
```

**Backend (Python packages):**
```bash
# Install in running container
docker-compose exec backend pip install <package-name>

# Update requirements.txt
echo "<package-name>==<version>" >> backend/requirements.txt

# Restart backend
docker-compose restart backend
```

### Database Migrations

Currently using SQLAlchemy's `create_all()` for simple auto-migration. For production, consider Alembic.

If models change:
1. Stop containers: `docker-compose down`
2. Delete volume: `docker volume rm accountingproject_postgres_data`
3. Restart: `docker-compose up --build`

**Note:** This wipes all data. For production, use proper migrations.

## Important Patterns and Gotchas

### Form Data vs JSON

- `/api/auth/login` expects FormData (OAuth2PasswordRequestForm)
- All other endpoints expect JSON
- 2FA verification endpoint accepts JSON body despite also needing credentials

### Router Navigation Guards

The router guard prevents infinite redirects by checking `to.path === from.path` before any navigation. This is critical for the auth flow.

### API Interceptor Auth Exclusions

The axios response interceptor must NOT redirect to /login when the failed request IS /login or /register. Check with:
```typescript
const isAuthRequest = error.config.url?.includes('/auth/login') ||
                     error.config.url?.includes('/auth/register')
```

### Token Expiration Strategy

Tokens expire at 23:59:59 on the day of creation, effectively providing day-long sessions that reset at midnight. This is implemented in `create_access_token()`.

### Styling Conventions

- Dark theme with gradient backgrounds
- Primary color: #00d4ff (cyan)
- Uses inline styles for component-specific styling
- Global styles in `frontend/src/style.css`
- Date/datetime picker calendar icon uses `filter: invert(1)` for white color

### Modal Pattern

Modals use:
```vue
<div v-if="showModal" class="modal">
  <div class="modal-content">
    <!-- Content -->
  </div>
</div>
```

Global `.modal` and `.modal-content` classes in style.css handle backdrop and positioning.

## Environment Configuration

**Backend Environment Variables** (set in docker-compose.yml):
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (MUST change in production)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token lifetime (not currently used due to custom expiration)

**CORS Origins:**
Hardcoded in `backend/app/main.py`. Update if frontend runs on different port:
```python
allow_origins=["http://localhost:5173", "http://localhost:3000"]
```

## Troubleshooting

**Frontend can't resolve imports after npm install:**
- Install package in container: `docker-compose exec frontend npm install <pkg>`
- Restart frontend: `docker-compose restart frontend`
- If still failing, rebuild: `docker-compose up --build frontend`

**Backend model changes not reflected:**
- Database uses auto-migration on startup
- Delete volume and restart to recreate schema (loses all data)

**401 errors on protected routes:**
- Check localStorage has valid token
- Verify token not expired (check browser console)
- Ensure `get_current_user` dependency is used on endpoint
- Check axios interceptor is attaching token to requests

**Login redirects even on failure:**
- Verify API interceptor excludes auth requests from redirect logic
- Check router guard doesn't create redirect loops
