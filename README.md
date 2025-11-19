# Accounting & Budgeting System

A full-stack web application for managing personal accounting and budgeting with user authentication.

## Features

- **User Authentication**: Secure login and registration with JWT tokens
- **Account Management**: Create and manage multiple accounts (asset, liability, equity, revenue, expense)
- **Transaction Tracking**: Record and track all financial transactions
- **Budget Planning**: Set and monitor budgets by category and time period
- **Dashboard**: Overview of accounts, balances, and recent transactions
- **User Isolation**: Each user can only access their own data

## Tech Stack

### Backend
- **Python 3.14.0**: Latest Python version
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: ORM for database operations
- **JWT**: Secure authentication
- **Pydantic**: Data validation

### Frontend
- **Vue 3**: Progressive JavaScript framework
- **Vite**: Fast build tool
- **Vue Router**: Client-side routing
- **Pinia**: State management
- **Axios**: HTTP client

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

## Project Structure

```
AccountingProject/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core configuration
│   │   ├── models/        # Database models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── main.py        # Application entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── views/         # Page views
│   │   ├── router/        # Routing configuration
│   │   ├── services/      # API services
│   │   ├── stores/        # Pinia stores
│   │   └── main.js        # Application entry point
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AccountingProject
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update the `.env` file with your configuration (especially change the SECRET_KEY for production)

4. Build and start the containers:
```bash
docker-compose up --build
```

5. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### First Time Setup

1. Register a new user account
2. Login with your credentials
3. Start creating accounts, transactions, and budgets

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info

### Accounts
- `GET /api/accounts/` - List all accounts
- `POST /api/accounts/` - Create new account
- `GET /api/accounts/{id}` - Get account details
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account

### Transactions
- `GET /api/transactions/` - List all transactions
- `POST /api/transactions/` - Create new transaction
- `GET /api/transactions/{id}` - Get transaction details
- `PUT /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction

### Budgets
- `GET /api/budgets/` - List all budgets
- `POST /api/budgets/` - Create new budget
- `GET /api/budgets/{id}` - Get budget details
- `PUT /api/budgets/{id}` - Update budget
- `DELETE /api/budgets/{id}` - Delete budget

## Development

### Running Backend Locally

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Running Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

## Database Schema

### Users
- id, email, username, hashed_password, created_at, updated_at

### Accounts
- id, name, account_type, balance, currency, description, user_id, created_at, updated_at

### Transactions
- id, description, amount, transaction_type, category, transaction_date, account_id, created_at, updated_at

### Budgets
- id, name, category, amount, spent, period, start_date, end_date, user_id, created_at, updated_at

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- User data isolation (users can only access their own data)
- CORS configured for frontend-backend communication

## Future Enhancements

- Export data to CSV/Excel
- Advanced reporting and analytics
- Multi-currency support
- Recurring transactions
- Budget alerts and notifications
- Mobile responsive design improvements

## License

MIT License
