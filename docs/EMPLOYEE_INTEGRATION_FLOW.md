# Employee Integration Data Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     EMPLOYEE MASTER FILE                        │
│                   (CSV/Excel Upload)                            │
│                                                                 │
│  First Name | Last Name | Email              | Title   | Function | Status  │
│  John       | Doe       | john.doe@company   | Engineer| Engineering | Active │
│  Jane       | Smith     | jane.smith@company | PM      | Product     | Active │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌─────────────────┐
                    │  Column Mapping │
                    │  Interface      │
                    └─────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     EMPLOYEES TABLE                              │
│  employee_id | first_name | last_name | email | title | dept | status │
│  1          | John       | Doe       | john... | ... | Eng  | Active │
│  2          | Jane       | Smith     | jane... | ... | Prod | Active │
│                                                                  │
│  Indexed on: email (UNIQUE)                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              AI TOOL USAGE DATA (OpenAI/BlueFlame)              │
│                                                                  │
│  email              | name         | dept (from tool) | messages │
│  john.doe@company   | John Doe     | [engineering]   | 100     │
│  contractor@ext.com | External User| [unknown]       | 80      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌─────────────────┐
                    │ normalize_*_data│
                    │ (with employee  │
                    │  lookup)        │
                    └─────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ↓                                           ↓
┌────────────────────┐                    ┌──────────────────────┐
│  EMPLOYEE FOUND    │                    │  NOT IN EMPLOYEE DB  │
│                    │                    │                      │
│  Use employee data:│                    │  Flag as:            │
│  - Department      │                    │  - Dept: "Unidentified│
│  - Full name       │                    │    User"             │
│  - Title           │                    │  - Name from tool    │
└────────────────────┘                    └──────────────────────┘
        │                                           │
        └─────────────────────┬─────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    USAGE_METRICS TABLE                           │
│                                                                  │
│  email              | user_name | department      | usage | cost │
│  john.doe@company   | John Doe  | Engineering     | 100   | $2.00│
│  contractor@ext.com | External  | Unidentified    | 80    | $1.60│
│                                  User                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DEPARTMENT MAPPER UI                          │
│                                                                  │
│  ⚠️ Unidentified Users (1)                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ contractor@ext.com | External User | 80 msgs | $1.60     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  📋 All Users                                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ John Doe | john.doe@company | ✅ Employee | 🔒 Engineering│  │
│  │ External | contractor@ext    | ⚠️ Unidentified | [Edit▼] │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Filter: ○ All Users  ○ Employees Only  ○ Unidentified Only    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Summary

1. **Employee Upload** → Employees table (single source of truth)
2. **Usage Data Upload** → Normalize with employee lookup
3. **Employee Found** → Use employee's department (override tool data)
4. **Not Found** → Flag as "Unidentified User"
5. **Department Mapper** → 
   - Employees: Read-only departments (🔒)
   - Unidentified: Editable mapping
   - Filter and search capabilities

## Key Queries

### Employee Lookup (During Normalization)
```sql
SELECT * FROM employees 
WHERE LOWER(email) = LOWER(?);
```

### Get Unidentified Users
```sql
SELECT 
    um.email,
    um.user_name,
    GROUP_CONCAT(DISTINCT um.tool_source) as tools_used,
    SUM(um.usage_count) as total_usage,
    SUM(um.cost_usd) as total_cost,
    COUNT(DISTINCT um.date) as days_active
FROM usage_metrics um
LEFT JOIN employees e ON LOWER(um.email) = LOWER(e.email)
WHERE e.email IS NULL AND um.email IS NOT NULL
GROUP BY um.email, um.user_name
ORDER BY total_usage DESC;
```

### Get Employee Departments (for mapper)
```sql
SELECT DISTINCT department 
FROM employees 
WHERE department IS NOT NULL 
ORDER BY department;
```

## Security & Compliance Benefits

```
┌─────────────────────────────────────────┐
│     UNIDENTIFIED USERS DETECTION        │
├─────────────────────────────────────────┤
│                                         │
│  ✅ Contractors using tools              │
│  ✅ External consultants                 │
│  ✅ Recently departed employees          │
│  ✅ Temporary access                     │
│  ✅ Shared/service accounts              │
│                                         │
│  → Easy audit trail                     │
│  → Cost attribution                     │
│  → Access review                        │
└─────────────────────────────────────────┘
```

## Update Flow

```
Employee File Re-upload
        │
        ↓
┌─────────────────┐
│ Upsert by email │  ← Existing employees updated
│ (INSERT/UPDATE) │  ← New employees added
└─────────────────┘
        │
        ↓
┌─────────────────────┐
│ Future usage data   │
│ gets new depts      │
└─────────────────────┘
        │
        ↓
┌─────────────────────┐
│ Historical data     │
│ keeps old depts     │
│ (not retroactive)   │
└─────────────────────┘
```
