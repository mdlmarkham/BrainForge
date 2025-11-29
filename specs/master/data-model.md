# Data Model: Security & Quality Remediation

**Feature**: Security Remediation  
**Date**: 2025-11-29  
**Status**: Complete

## Entity Definitions

### User Authentication Entity

**Table**: `users`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key | Unique user identifier |
| username | String(255) | Unique, Not Null, Indexed | User login name |
| email | String(255) | Unique, Not Null, Indexed | User email address |
| hashed_password | String(255) | Not Null | bcrypt hashed password |
| is_active | Boolean | Default: True | Account activation status |
| created_at | DateTime | Default: now() | Account creation timestamp |
| updated_at | DateTime | Default: now() | Last update timestamp |

**Relationships**:
- One-to-many with audit trails (user actions)
- One-to-many with agent runs (user-initiated research)

**Validation Rules**:
- Username: 3-50 characters, alphanumeric and underscores only
- Email: Valid email format, case-insensitive uniqueness
- Password: Minimum 8 characters, complexity requirements enforced

### JWT Token Payload

**Structure**: JWT claims for authentication

| Claim | Type | Description |
|-------|------|-------------|
| sub | String | User ID (UUID string) |
| exp | DateTime | Token expiration time |
| iat | DateTime | Token issuance time |
| scope | String[] | Optional: User permissions |

### Rate Limiting Configuration

**Storage**: Redis keys with sliding window counters

| Key Pattern | Data Type | Description |
|-------------|-----------|-------------|
| `rate_limit:{user_id}:{endpoint}` | Integer | Request count for user-endpoint pair |
| `rate_limit:{ip}:{endpoint}` | Integer | Request count for IP-endpoint pair |

## State Transitions

### User Account Lifecycle

1. **Registration**: User created with hashed password, is_active=true
2. **Activation**: Email verification (future enhancement)
3. **Authentication**: JWT token issued on successful login
4. **Deactivation**: is_active=false, existing tokens invalidated
5. **Reactivation**: is_active=true, new tokens required

### Authentication Flow

1. **Login Request**: Username/password validation
2. **Token Generation**: JWT created with user ID and expiration
3. **API Access**: Token validated on each request
4. **Token Refresh**: New token issued before expiration (future enhancement)

### Rate Limiting States

1. **Normal**: Request count below threshold
2. **Warning**: Request count approaching threshold (logging)
3. **Limited**: Request count exceeded (429 response)

## Security Constraints

### Password Policy
- Minimum length: 8 characters
- Complexity: At least one uppercase, one lowercase, one number
- Hashing: bcrypt with work factor 12
- No password reuse tracking (future enhancement)

### Token Security
- Expiration: 24 hours default (configurable)
- Algorithm: HS256 with secure secret key
- No token blacklisting (stateless design)
- Secure secret rotation required in production

### Access Control
- All API endpoints require authentication by default
- Public endpoints explicitly configured
- Role-based permissions (future enhancement)

## Migration Strategy

### Database Changes
- New `users` table with authentication fields
- No modifications to existing tables
- Backward compatibility maintained for existing data

### Data Integrity
- Foreign key constraints preserved
- Existing relationships unchanged
- Audit trails maintained for security actions

## Constitutional Compliance

All data model decisions align with BrainForge constitution:

- **Structured Data Foundation**: Clear user authentication schema
- **AI Agent Integration**: Authentication preserves agent functionality
- **Versioning & Auditability**: User actions logged with timestamps
- **Roles & Permissions**: Clear user role definitions
- **Data Governance**: Secure credential storage and handling