# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack accounting and budgeting application with FastAPI backend, Vue 3 frontend, and PostgreSQL database. All services containerized with Docker Compose. Features include user authentication with optional 2FA, multi-currency account management, transaction tracking with category management, and budget planning.

## Development Commands

### Environment Setup

**Quick Start:**
```bash
# For local development
cp .env.development .env
docker-compose up --build

# For production deployment
cp .env.production .env
# Edit .env to add real credentials
docker-compose -f docker-compose.prod.yml up -d --build
```

See `DEPLOYMENT.md` for detailed deployment instructions.

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

**Access Points (Development):**
- Frontend: http://localhost (nginx proxy to Vite dev server)
- Frontend Direct (dev): http://localhost:5173 (with HMR enabled)
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs (development only)
- Database: localhost:5432 (user: accounting_user, db: accounting_db)

**Access Points (Production):**
- Application: https://accounting.yshongcode.com
- Backend API: https://accounting.yshongcode.com/api
- Database: Internal only (not exposed)

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
- `Budget` ↔ many-to-many ↔ `Account` (via `BudgetAccount` junction table)
- `Budget` ↔ many-to-many ↔ `Category` (via `BudgetCategory` junction table)

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

### Frontend Architecture (Vue 3 + Vite + Pinia + Composables)

**State Management (Pinia Stores):**
- `auth.ts`: Authentication state, JWT token (persisted in localStorage)
- `accounts.ts`: Account CRUD operations and state
- `transactions.ts`: Transaction CRUD operations and state
- `budgets.ts`: Budget CRUD operations, helper functions (getPeriodText, getAccountNames)
- `categories.ts`: Category CRUD operations including reordering
- Pattern: Composition API with `defineStore`, reactive `ref()` state, async functions

**Composables (Reusable Logic):**
- `useModal.ts`: Modal visibility and error state management
- `useConfirm.ts`: Confirmation dialog handling with callbacks
- `useMessage.ts`: Success/error message display
- `useForm.ts`: Generic form state management with editing support
- `useBudgetForm.ts`: Budget-specific form logic (date range, range mode)
- `useDashboard.ts`: Dashboard calculations (totals, budget status, daily spending)
- `useDateTime.ts`: Centralized date/time formatting utilities

**Architectural Pattern:**
Views import stores and composables to avoid code duplication. All business logic lives in stores or composables, not in components.

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

### Budget Multi-Account Binding Architecture

**Overview:**
Budgets support flexible account binding:
- Can bind to multiple accounts (track spending across specific accounts)
- Can bind to zero accounts (track spending across ALL user's accounts)
- Uses many-to-many relationship via `BudgetAccount` junction table

**Implementation Pattern:**

```python
# Backend - backend/app/models/budget_account.py
class BudgetAccount(Base):
    """預算與帳戶的多對多關聯表"""
    __tablename__ = "budget_accounts"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
```

```python
# Budget model relationship
class Budget(Base):
    # No direct account_id column
    accounts = relationship("Account", secondary="budget_accounts", backref="budgets")
```

**Spent Calculation Logic:**
```python
def calculate_budget_spent(db: Session, budget: Budget) -> float:
    account_ids = [acc.id for acc in budget.accounts]

    if account_ids:
        # Budget bound to specific accounts - only count those
        query = query.filter(Transaction.account_id.in_(account_ids))
    else:
        # No account binding - count ALL user's accounts
        user_account_ids = db.query(Account.id).filter(Account.user_id == budget.user_id).all()
        query = query.filter(Transaction.account_id.in_(user_account_ids))
```

**CRITICAL: SQLAlchemy Eager Loading Pattern**
Always use `joinedload()` when querying budgets to prevent lazy loading issues:

```python
from sqlalchemy.orm import joinedload

# Correct - eager loads accounts relationship
budgets = db.query(Budget).options(joinedload(Budget.accounts)).filter(...).all()

# Wrong - accounts relationship not loaded, budget.accounts returns empty list
budgets = db.query(Budget).filter(...).all()
```

**Frontend Schema:**
```typescript
export interface Budget {
    account_ids: number[]  // Empty array = all accounts
    // ... other fields
}
```

**Recurring Budget Behavior:**
When auto-generating next period budgets (`backend/app/tasks/budget_recurring.py`), both account bindings and category bindings are copied from the previous period.

### Budget Multi-Category Binding Architecture

**Overview:**
Budgets support flexible category binding (added alongside multi-account binding):
- Can bind to multiple categories (track spending across specific categories)
- Can bind to zero categories (track spending across ALL categories)
- Uses many-to-many relationship via `BudgetCategory` junction table

**Implementation Pattern:**

```python
# Backend - backend/app/models/budget_category.py
class BudgetCategory(Base):
    """預算與類別的多對多關聯表"""
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    category_name = Column(String, nullable=False)  # Stores category name directly
```

**Key Difference from Account Binding:**
- Account binding uses ForeignKey to `accounts.id` (references Account table)
- Category binding uses `category_name` String (no FK, flexible for user-defined categories)

**Spent Calculation Logic:**
```python
def calculate_budget_spent(db: Session, budget: Budget, category_names: List[str] = None) -> float:
    # ... account filtering logic ...

    # If category_names provided and not empty, filter by those categories
    if category_names and len(category_names) > 0:
        query = query.filter(Transaction.category.in_(category_names))

    # Empty list = all categories included
    spent = query.scalar()
    return spent or 0.0
```

**Frontend Schema:**
```typescript
export interface Budget {
    account_ids: number[]        // Empty array = all accounts
    category_names: string[]     // Empty array = all categories
    // ... other fields
}
```

**Multi-Select UI Pattern:**
Both accounts and categories use checkbox-based multi-select interfaces in the budget form, consistent with the account binding pattern.

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
- Budget forms use checkbox-based multi-select for category binding
- Drag-and-drop reordering using Sortable.js library
- Management modal allows add/edit/delete/reorder
- Changes immediately sync to backend

### Reports System

**Overview:**
Comprehensive reporting endpoints at `/api/reports` provide data analytics for specified date ranges.

**Available Reports:**
- `/overview`: Summary with category breakdown, top 5 income/expense transactions
- `/details`: Daily transaction lists with totals
- `/category`: Category-based spending analysis with percentages
- `/ranking`: Top expense and income transactions (configurable limit)
- `/account`: Account-based spending analysis with balances
- `/monthly-stats`: Daily statistics for a specific month (for charts)

**Features:**
- All reports require `start_date` and `end_date` query parameters
- Returns aggregated data with percentages, rankings, and totals
- Supports filtering by category and account
- Data formatted for frontend charts and visualizations

## Reusable Components

### Calculator Component

**Location:** `frontend/src/components/Calculator.vue`

**Purpose:** Provides an in-app calculator for amount input fields with basic arithmetic operations.

**Features:**
- Basic operations: +, -, *, / (displayed as +, −, ×, ÷)
- Number pad (0-9), decimal point support
- Clear (C) and backspace (←) functions
- Dual-display: shows both expression and current value
- Results automatically rounded to 2 decimal places
- Division by zero prevention (displays "Error")
- Beautiful dark theme matching application style

**Usage Pattern:**

```vue
<template>
  <!-- Amount input field with calculator button -->
  <div style="position: relative;">
    <input
      type="number"
      v-model.number="form.amount"
      @focus="showCalculator = true"
      style="padding-right: 40px;"
    />
    <button
      type="button"
      @click="showCalculator = true"
      style="position: absolute; right: 5px; ..."
      title="打開計算機"
    >
      🧮
    </button>
  </div>

  <!-- Calculator component -->
  <Calculator
    v-model="showCalculator"
    :initial-value="form.amount"
    @confirm="handleCalculatorConfirm"
  />
</template>

<script setup lang="ts">
import Calculator from '@/components/Calculator.vue'

const showCalculator = ref(false)

const handleCalculatorConfirm = (value: number) => {
  form.value.amount = value
}
</script>
```

**Props:**
- `modelValue: boolean` - Controls calculator visibility
- `initialValue?: number` - Pre-fills calculator with existing value

**Events:**
- `update:modelValue` - Emitted when closing calculator
- `confirm` - Emitted with calculated value when user confirms

**Current Usage:**
- Transaction creation/edit form (`frontend/src/views/Transactions.vue`)
- Dashboard quick transaction modal (`frontend/src/views/Dashboard.vue`)

### Modal Components

**ConfirmModal** (`frontend/src/components/ConfirmModal.vue`):
- Used for confirmation dialogs (delete operations, etc.)
- Props: title, message, confirmText, cancelText, confirmType

**MessageModal** (`frontend/src/components/MessageModal.vue`):
- Used for success/error messages
- Props: type ('success' | 'error'), message

**CategoryManagementModal** (`frontend/src/components/CategoryManagementModal.vue`):
- Dedicated modal for category CRUD operations
- Includes drag-and-drop reordering with Sortable.js

**Usage Pattern:**
All modals follow the same v-model pattern for visibility control:

```vue
<ConfirmModal
  v-model="showConfirmModal"
  title="確認刪除"
  message="確定要刪除此交易嗎？"
  @confirm="handleConfirm"
/>
```

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
- Types: cash, bank, credit_card, stored_value, securities, other

`Transaction`:
- id, description, amount, transaction_type, category, transaction_date
- account_id (FK), created_at, updated_at
- Types: credit (income), debit (expense)

`Budget`:
- id, name, category (nullable, legacy field), amount, spent, daily_limit, range_mode, period, start_date, end_date
- user_id (FK), parent_budget_id (FK, for recurring budgets), created_at, updated_at
- Range modes: recurring (auto-generates next period), custom (one-time date range)
- Periods (for recurring mode): monthly, quarterly, yearly
- **Note:** No direct account_id column - uses many-to-many via BudgetAccount
- **Note:** No direct category column - uses many-to-many via BudgetCategory (category field kept for backward compatibility)

`BudgetAccount`:
- id, budget_id (FK), account_id (FK), created_at
- Junction table for Budget-Account many-to-many relationship

`BudgetCategory`:
- id, budget_id (FK), category_name, created_at
- Junction table for Budget-Category many-to-many relationship
- Stores category name directly (no FK) for flexibility

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

### Date/Time Formatting

**Critical:** Date strings from backend may include UTC "Z" marker and milliseconds. Always use the centralized formatting utilities:

```typescript
// frontend/src/utils/dateFormat.ts

// Display format: "2025-11-19 12:00:00"
formatDateTime(dateString: string)  // Removes Z and milliseconds, replaces T with space

// Backend format: "2025-11-19T14:30:00"
formatDateTimeForBackend(dateTimeLocal: string)  // Adds :00 seconds if missing

// Input format: "2025-11-19T14:30"
formatDateTimeForInput(dateString: string)  // Truncates to datetime-local format
```

**Common Mistake:**
```typescript
// Wrong - doesn't handle Z marker
dateString.replace('T', ' ')

// Correct - uses utility function
formatDateTime(dateString)
```

## Environment Configuration

**Backend Environment Variables** (set in docker-compose.yml or .env):
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (MUST change in production)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token lifetime (not currently used due to custom expiration)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
- `ENVIRONMENT`: `development` or `production` (controls API docs visibility)
- `RATE_LIMIT_ENABLED`: Enable rate limiting (default: true)
- `RATE_LIMIT_PER_MINUTE`: Requests per minute per IP (default: 60)
- `ENABLE_SECURITY_HEADERS`: Enable security headers (default: true)

**CORS Origins:**
Configured via `ALLOWED_ORIGINS` environment variable, parsed in `backend/app/core/config.py`:
```python
# Environment variable
ALLOWED_ORIGINS=http://localhost,http://localhost:5173,https://yourdomain.com
```

## Security Features

**Rate Limiting:**
- Custom middleware in `main.py` tracks requests per IP address
- Configurable via `RATE_LIMIT_ENABLED` and `RATE_LIMIT_PER_MINUTE`
- Returns 429 status when limit exceeded
- Requests tracked per minute with automatic cleanup

**Security Headers:**
When `ENABLE_SECURITY_HEADERS=true`, the following headers are added:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'; ...`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

**Production Deployment:**
- Nginx reverse proxy handles TLS termination and request routing
- Backend/frontend containers exposed only internally (not on host ports)
- API docs (`/docs`, `/redoc`) disabled in production mode
- Database port should not be exposed in production (remove from docker-compose.yml)
- SSL certificates should be placed in `nginx/ssl/` directory

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

**Budget spent amount not updating:**
- Ensure budgets are queried with `joinedload(Budget.accounts)` to eager load relationships
- Without eager loading, `budget.accounts` will be an empty list even when accounts are bound
- See Budget Multi-Account Binding Architecture section for correct pattern

**Dates showing "Z" or timezone markers:**
- Use `formatDateTime()` utility from `frontend/src/utils/dateFormat.ts`
- This function properly removes UTC markers and milliseconds
- Always use centralized formatting utilities, not manual string replacement

**Transaction operations not updating budget spent amounts:**
- After creating/updating/deleting transactions, both accounts AND budgets must be refreshed
- Correct pattern in `Transactions.vue`:
```typescript
await Promise.all([
  accountsStore.fetchAccounts(),
  budgetsStore.fetchBudgets()  // CRITICAL: Must also refresh budgets
])
```
- Missing `budgetsStore.fetchBudgets()` causes stale budget data on the dashboard

**Custom categories not affecting budget calculations:**
- Ensure the `calculate_budget_spent()` function filters by category correctly
- Should use `category_names IN (...)` for multi-category support
- Empty `category_names` list means "all categories"
- Never include uncategorized transactions in category-specific budgets
