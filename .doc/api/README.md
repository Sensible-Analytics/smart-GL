# Smart GL API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
Currently: None (development mode)
Future: Bearer token via Supabase Auth

## Endpoints

### Health Check

**GET** `/health`

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### Transactions

**GET** `/transactions`

Query parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| limit | int | Max results (default: 50) |
| offset | int | Pagination offset |
| category_id | uuid | Filter by category |
| start_date | date | Filter from date |
| end_date | date | Filter to date |

Response:
```json
{
  "items": [
    {
      "id": "uuid",
      "date": "2024-01-15",
      "description": "Coffee shop",
      "amount": 550,
      "currency": "AUD",
      "category_id": "uuid",
      "category_name": "Meals & Entertainment",
      "account_id": "uuid",
      "account_name": "Business Account"
    }
  ],
  "total": 100
}
```

**POST** `/transactions/{id}/categorise`

Body:
```json
{
  "category_id": "uuid"
}
```

### Journal

**GET** `/journal`

Query parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| transaction_id | uuid | Filter by transaction |
| start_date | date | Filter from date |
| end_date | date | Filter to date |

Response:
```json
{
  "items": [
    {
      "id": "uuid",
      "transaction_id": "uuid",
      "account_id": "uuid",
      "account_code": "200",
      "account_name": "Accounts Receivable",
      "debit": 0,
      "credit": 10000,
      "date": "2024-01-15"
    }
  ]
}
```

### Reports

**GET** `/reports/balance-sheet`

Query parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| date | date | As of date |

**GET** `/reports/profit-loss`

Query parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | date | Period start |
| end_date | date | Period end |

### Accounts

**GET** `/accounts`

Response:
```json
{
  "items": [
    {
      "id": "uuid",
      "code": "100",
      "name": "Cash at Bank",
      "type": "asset",
      "normal_balance": "debit",
      "parent_id": null
    }
  ]
}
```

**POST** `/accounts`

Body:
```json
{
  "code": "200",
  "name": "Accounts Receivable",
  "type": "asset",
  "parent_id": "uuid"
}
```

### Bank Feeds (Basiq)

**POST** `/basiq/connect`

Body:
```json
{
  "institution_id": "AU00001",
  "access_token": "string"
}
```

**GET** `/basiq/accounts`

**GET** `/basiq/transactions`

### AI Categorisation

**GET** `/categorise/stats`

Returns categorisation accuracy metrics.

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limits

Development: None
Production: 100 requests/minute