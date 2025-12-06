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

For production deployment, see docker-compose.prod.yml and Environment Configuration section below.

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

**Architecture Differences:**

*Development Mode* (`docker-compose.yml`):
- Frontend: Vite dev server with HMR (Hot Module Replacement)
- Dockerfile: `frontend/Dockerfile`
- Port: 5173
- Benefits: Fast refresh, debugging tools, source maps

*Production Mode* (`docker-compose.prod.yml`):
- Frontend: Docker 內構建 → 透過 volume 共享靜態檔案給 Nginx
- Frontend Builder: 使用 `Dockerfile.prod` 構建並輸出到 `frontend-dist` volume
- Nginx: 掛載 `frontend-dist` volume 服務靜態檔案
- Benefits: 完全自動化構建，無需手動步驟，優化的 bundle
- Flow:
  1. `frontend-builder` 容器構建靜態檔案 → 輸出到 `frontend-dist` volume
  2. Main Nginx (port 8080) 掛載 `frontend-dist` volume + 代理 `/api` 到 Backend (port 8000)

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

# Run E2E tests (Playwright)
npm run test:e2e
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

**Google OAuth Integration:**
- Uses Authlib for OAuth2 authentication with Google
- Login endpoint: `/api/login/google` (initiates OAuth flow)
- Callback endpoint: `/api/auth/google/callback` (handles OAuth response)
- Auto-creates users with `is_google_user=True` flag (no password required)
- Auto-creates default accounts (現金, 預設銀行) for new Google users
- Environment variables: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- HTTPS redirect handling for production environments
- Redirects to frontend with JWT token: `{FRONTEND_URL}/google-callback?token={token}`

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
- `useDateTime.ts`: Wrapper composable that exports date utilities from `utils/dateFormat.ts`
- `useLoading.ts`: Loading state management for async operations

**Date/Time Utilities:**
- Location: `frontend/src/utils/dateFormat.ts`
- `formatDateTime()`: Display format (removes Z marker, milliseconds, replaces T with space)
- `formatDateTimeForBackend()`: Backend format (adds :00 seconds if missing)
- `formatDateTimeForInput()`: datetime-local input format (truncates to minutes)
- Also exported through `useDateTime()` composable for convenience

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

### Password Reset System

**Overview:**
Full password reset functionality using Gmail SMTP with secure one-time tokens.

**Key Features:**
- Secure token-based password reset (30-minute expiration by default)
- HTML email templates matching app design (dark theme, cyan accents)
- Gmail SMTP integration with app passwords
- Anti-enumeration protection (same response regardless of email existence)

**Implementation:**
- Model: `PasswordResetToken` (backend/app/models/password_reset_token.py)
- Endpoints:
  - `POST /api/password-reset/request` - Request reset email
  - `GET /api/password-reset/verify-token/{token}` - Validate token
  - `POST /api/password-reset/confirm` - Set new password
- Email service: `backend/app/core/email.py` (SMTP configuration)

**Setup:**
See `PASSWORD_RESET_GUIDE.md` for detailed Gmail SMTP configuration, including:
- How to enable Google 2-step verification
- How to generate app passwords
- Environment variable setup

**Environment Variables:**
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`
- `FRONTEND_URL` (for generating reset links)
- `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` (default: 30)

**Security:**
- Tokens generated with `secrets.token_urlsafe(32)` (43 characters, high entropy)
- One-time use tokens (marked `is_used=true` after consumption)
- Automatic expiration tracking in database
- Password strength validation on reset (same rules as registration)

### Exchange Rate Crawler

**Overview:**
Automated exchange rate fetching from Taiwan Bank of Taiwan website.

**Implementation:**
- Service: `backend/app/services/crawler.py`
- Uses BeautifulSoup to scrape BOT exchange rate table
- Stores rates in `ExchangeRate` model (currency_code, currency_name, buying_rate, selling_rate)
- Updates existing rates or creates new entries

**Data Source:**
- URL: https://rate.bot.com.tw/xrt?Lang=zh-TW
- Extracts spot buying/selling rates (即期匯率)
- Handles currencies without spot rates gracefully

**Usage:**
Called by scheduled tasks or can be triggered manually. Enables multi-currency account balance calculations.

### Installment Transaction System

**Overview:**
Full-featured installment (分期) transaction system with support for both zero-interest and interest-bearing installments.

**Key Features:**
- Installment periods: 2-60 periods
- Billing day selection (1-31)
- Zero-interest installments use integer division (remainder goes to first period)
- Interest-bearing installments use loan payment formula for annual rate ≥ 1%
- Optional "exclude from budget" flag
- Auto-generates note with installment details
- Delete modes: single transaction or entire group

**Implementation:**

```python
# Loan payment formula for interest-bearing installments
if annual_rate >= 1:
    monthly_rate = annual_rate / 12 / 100
    monthly_payment = total_amount * monthly_rate * ((1 + monthly_rate) ** num_installments) / (((1 + monthly_rate) ** num_installments) - 1)
    base_amount = int(monthly_payment)
    total_with_interest = int(monthly_payment * num_installments)
    last_installment_amount = total_with_interest - total_paid_before_last
```

**Transaction Fields:**
- `is_installment`: Boolean flag
- `installment_group_id`: UUID for grouping related installments
- `installment_number`: Current period number (e.g., 2 of 12)
- `total_installments`: Total number of periods
- `total_amount`: Original principal amount
- `remaining_amount`: Amount remaining AFTER this payment
- `annual_interest_rate`: Annual interest rate percentage
- `exclude_from_budget`: Whether to exclude from budget calculations

**Frontend Display:**
- Transaction calendar shows period progress (e.g., "2/12")
- Shows remaining periods, remaining amount, and interest rate
- Installment info displayed with cyan color scheme
- Delete modal offers two options: delete single or delete entire group

**Calculation Notes:**
- Zero-interest: Uses `Math.floor()` for integer division
- Interest-bearing: Last period calculated separately to handle rounding
- Display uses "≈" symbol to indicate estimated amounts
- Auto-generated notes include breakdown of principal, interest, and total

### Recurring Expense System

**Overview:**
Automated monthly expense system that creates transactions on specified days each month.

**Key Features:**
- User selects day of month (1-31) for automatic transaction creation
- System finds next occurrence from today and creates monthly transactions
- Scheduled task runs daily at 00:01 to create due transactions
- Three delete modes: single, future, or all
- Purple color scheme to distinguish from regular transactions

**Implementation:**

**Backend:**
- Model: `RecurringExpense` (backend/app/models/recurring_expense.py)
- Fields: description, amount, category, note, day_of_month, account_id, recurring_group_id, start_date, end_date, is_active, last_executed_date
- Service: `recurring_expense_processor.py` (backend/app/services/)
- Scheduler: Runs daily at 00:01 via APScheduler

**Transaction Lifecycle:**
1. User creates recurring expense with day_of_month
2. System calculates next occurrence from today
3. Scheduled task checks daily for due recurring expenses
4. Creates transaction when date arrives
5. Updates account balance and last_executed_date
6. Transaction marked with `is_from_recurring=True` and `recurring_group_id`

**Delete Modes:**
- **single**: Delete one transaction only (reverses balance if date passed)
- **future**: Delete this transaction and all future ones (sets end_date, deactivates recurring expense)
- **all**: Delete all transactions and the recurring expense itself

**Frontend Integration:**
- Checkbox option in transaction form (only for debit type)
- Purple background for recurring expense fields
- Transactions display "[未生效]" tag if date hasn't arrived yet
- Transactions display "[固定支出]" tag if already effective
- Delete modal shows three options for recurring expense transactions

**Important Logic:**
```python
def should_create_transaction(recurring_expense, target_date, today):
    # Only create if:
    # 1. Target date has arrived (today >= target_date)
    # 2. Not executed this month yet
    if today < target_date:
        return False

    if recurring_expense.last_executed_date:
        last_executed_local = recurring_expense.last_executed_date.astimezone(TAIPEI_TZ).date()
        # Skip if already executed this month
        if (last_executed_local.year == target_date.year and
            last_executed_local.month == target_date.month):
            return False

    return True
```

**Edge Cases:**
- Month-end handling: Feb 30 → Feb 28/29 (last day of month)
- Timezone: All dates stored in UTC, displayed in Taipei timezone
- Note format: Auto-appends "固定支出 - 每月 X 號" to user's note

### Background Tasks

**Location:** `backend/app/tasks/` and scheduler in `backend/app/core/scheduler.py`

**Budget Recurring Tasks** (`budget_recurring.py`):
- Auto-generates next period budgets for recurring budgets
- Copies account bindings and category bindings from previous period
- Triggered by scheduler (APScheduler) or manually
- Handles monthly, quarterly, and yearly recurring budgets

**Recurring Expense Processor** (`recurring_expense_processor.py`):
- Runs daily at 00:01 (configured in scheduler)
- Checks all active recurring expenses
- Creates transactions for expenses whose day_of_month has arrived
- Updates account balances automatically
- Tracks last_executed_date to prevent duplicates
- Handles month-end edge cases (e.g., day 31 in Feb → last day)

**Exchange Rate Crawlers:**
- BOT (Bank of Taiwan): Runs hourly
- E.SUN Bank: Runs hourly
- Both use BeautifulSoup to scrape exchange rates
- Stores in ExchangeRate model for multi-currency support

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

**DailyTransactionsModal** (`frontend/src/components/DailyTransactionsModal.vue`):
- Displays all transactions for a specific day
- Shows daily totals and transaction list
- Allows editing transactions from the calendar view

**TransactionsSearchModal** (`frontend/src/components/TransactionsSearchModal.vue`):
- Advanced transaction search with filters
- Filters by date range, category, account, amount range
- Displays search results with edit capability

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

### Utility Components

**LoadingSpinner** (`frontend/src/components/LoadingSpinner.vue`):
- Displays loading animation during async operations
- Controlled via `useLoading()` composable

**DateTimeInput** (`frontend/src/components/DateTimeInput.vue`):
- Standardized datetime input with proper formatting
- Handles timezone conversion automatically

**DescriptionHistory** (`frontend/src/components/DescriptionHistory.vue`):
- Dropdown showing historical transaction descriptions
- Allows quick selection of previously used descriptions

**CategorySelector** (`frontend/src/components/CategorySelector.vue`):
- Reusable category dropdown with consistent styling
- Supports category management integration

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
- Types: credit (income), debit (expense), installment (分期)
- Installment fields: is_installment, installment_group_id, installment_number, total_installments, total_amount, remaining_amount, annual_interest_rate, exclude_from_budget
- Recurring expense fields: recurring_group_id, is_from_recurring

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

`PasswordResetToken`:
- id, email, token (unique), is_used, created_at, expires_at
- Used for password reset functionality

`ExchangeRate`:
- id, currency_code, currency_name, buying_rate, selling_rate, updated_at
- Stores exchange rates from Taiwan Bank of Taiwan

`RecurringExpense`:
- id, description, amount, category, note, day_of_month, account_id
- recurring_group_id (unique UUID), start_date, end_date, is_active, last_executed_date
- user_id (FK via account), created_at, updated_at
- Used for automated monthly expense transactions

**Additional User Fields:**
- `is_google_user` (Boolean): Indicates OAuth user (no password)
- `is_blocked` (Boolean): Admin can block users
- `last_login_at` (DateTime): Tracks last login timestamp

## Common Development Workflows

### Refactoring Large Components

When a component becomes too large (>1000 lines), follow this refactoring pattern:

**1. Extract Composables for Business Logic:**
```typescript
// Before: All logic in component <script setup>
const handleSubmit = async () => {
  // Complex validation and API calls
}

// After: Extract to composable
// composables/useTransactionForm.ts
export function useTransactionForm() {
  const formData = ref({ ... })
  const validate = () => { ... }
  const submit = async () => { ... }
  return { formData, validate, submit }
}
```

**2. Extract Child Components for UI:**
- Modal content → separate modal components
- Form sections → form field components
- Repeated UI patterns → reusable components

**3. Critical: Pass Refs Correctly**
```vue
<!-- Parent component -->
<script setup>
const form = useTransactionForm()  // Returns refs
</script>

<template>
  <!-- Pass ref object, not .value -->
  <ChildComponent :data="form.formData" />  <!-- Vue will unwrap -->
</template>
```

**4. Maintain Single Source of Truth:**
- Don't duplicate state between parent and child
- Use props for data down, events for actions up
- Use composables for shared reactive state

**5. Test After Each Extraction:**
- Extract one piece at a time
- Test functionality after each extraction
- Don't batch multiple extractions before testing

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

### Vue 3 Ref Unwrapping in Templates

**CRITICAL PATTERN:** Vue 3 automatically unwraps refs in templates. When using composables that return refs, DO NOT use `.value` in template expressions.

```vue
<script setup>
import { useTransactionForm } from '@/composables/useTransactionForm'

const form = useTransactionForm()
// form.isTransfer is a computed ref
// form.isRecurring is a ref
</script>

<template>
  <!-- CORRECT - refs unwrap automatically in templates -->
  <div v-if="form.isTransfer">Transfer UI</div>
  <input v-model="form.isRecurring" type="checkbox" />

  <!-- WRONG - will cause "true is not a function" errors -->
  <div v-if="form.isTransfer.value">Transfer UI</div>
  <input v-model="form.isRecurring.value" type="checkbox" />
</template>
```

**Common Mistake Patterns:**
```vue
<!-- ❌ WRONG - causes TypeError -->
<div v-if="form.isEditing.value">
<input v-model="form.formData.value.amount" />

<!-- ✅ CORRECT - Vue unwraps refs automatically -->
<div v-if="form.isEditing">
<input v-model="form.formData.value.amount" />  <!-- formData itself needs .value -->
```

**When to use `.value`:**
- In `<script setup>` code: Always use `.value` to access/modify refs
- In templates with composable refs: NEVER use `.value` on the ref itself
- Exception: Nested reactive objects like `form.formData.value.amount` - the parent ref needs `.value`, but composable refs at the top level don't

**Why this matters:**
Using `.value` in templates on composable refs causes runtime errors like "TypeError: true is not a function" because Vue's template compiler expects raw refs, not their unwrapped values.

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
- `FRONTEND_URL`: Frontend URL for OAuth callbacks and password reset links
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`: Gmail SMTP configuration
- `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`: Email sender information
- `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`: Password reset token expiration (default: 30)

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
- The `useDateTime()` composable re-exports these utilities for convenience

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

**Google OAuth redirect issues:**
- Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in .env
- In production, redirect URIs must use HTTPS
- The callback URL must be registered in Google Cloud Console
- Frontend must handle `/google-callback?token={token}` route to extract JWT and store in localStorage

**Installment transactions not calculating correctly:**
- Check if `annual_interest_rate` is set for interest-bearing installments
- Verify loan payment formula is using monthly rate (annual / 12 / 100)
- Ensure last period is calculated separately to handle rounding
- Zero-interest should use `Math.floor()` for integer division
- Check that remainder goes to FIRST period, not last

**Recurring expense transactions not being created:**
- Verify scheduler is running (check logs for "Scheduler started")
- Confirm recurring expense `is_active=True` and no `end_date` set
- Check `last_executed_date` - should be null or from previous month
- Ensure `day_of_month` is valid for current month (handle Feb 30 → Feb 28/29)
- Verify scheduled task runs at 00:01 daily in scheduler configuration
- Check transaction creation logic in `recurring_expense_processor.py`

**Recurring expense transactions show wrong "未生效" status:**
- Frontend uses `isTransactionPending()` function to check if date has arrived
- Must compare transaction_date with current date in Taipei timezone
- Transaction is pending if `transaction_date > now`
- Once date arrives, display changes from "[未生效]" to "[固定支出]"

**TypeError: "true is not a function" or similar errors:**
- This occurs when using `.value` on composable refs in Vue templates
- Vue 3 automatically unwraps refs in templates - DO NOT use `.value`
- Check v-model bindings: `v-model="form.isRecurring"` NOT `v-model="form.isRecurring.value"`
- Check v-if conditions: `v-if="form.isTransfer"` NOT `v-if="form.isTransfer.value"`
- See "Vue 3 Ref Unwrapping in Templates" section for detailed patterns
- Exception: Nested objects like `form.formData.value.amount` still need parent ref's `.value`
