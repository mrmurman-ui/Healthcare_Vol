```mermaid
erDiagram
    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        enum role
        string province
        string district
        string subdistrict
        bool is_active
        datetime created_at
        datetime updated_at
        string created_by
        string updated_by
    }

    VOLUNTEERS {
        uuid id PK
        string volunteer_code UK
        string full_name
        string phone
        string email
        string province
        string district
        string subdistrict
        string village
        string position
        enum status
        string photo_url
        datetime created_at
        datetime updated_at
        string created_by
        string updated_by
    }

    HOUSEHOLDS {
        uuid id PK
        string household_code UK
        string address
        string village
        string community
        string subdistrict
        string district
        string province
        float latitude
        float longitude
        string head_of_household
        string phone
        enum income_group
        enum housing_type
        datetime created_at
        datetime updated_at
        string created_by
        string updated_by
    }

    CITIZENS {
        uuid id PK
        uuid household_id FK
        string full_name
        enum gender
        date date_of_birth
        string occupation
        string education
        string phone
        bool is_elderly
        bool is_disabled
        bool is_bedridden
        bool is_pregnant
        bool is_living_alone
        datetime created_at
        datetime updated_at
        string created_by
        string updated_by
    }

    HOME_VISITS {
        uuid id PK
        uuid citizen_id FK
        uuid volunteer_id FK
        date visit_date
        enum visit_type
        text observation
        text recommendation
        float latitude
        float longitude
        text photo_urls
        datetime created_at
        datetime updated_at
        string created_by
        string updated_by
    }

    REFERRALS {
        uuid id PK
        uuid citizen_id FK
        uuid volunteer_id FK
        date referral_date
        enum target
        string target_name
        text reason
        enum status
        text outcome
        date followup_date
        text followup_notes
        datetime created_at
        datetime updated_at
        string created_by
        string updated_by
    }

    AUDIT_LOGS {
        uuid id PK
        string actor
        string action
        string resource_type
        string resource_id
        text detail
        datetime created_at
    }

    HOUSEHOLDS ||--o{ CITIZENS : "contains"
    CITIZENS ||--o{ HOME_VISITS : "visited by"
    VOLUNTEERS ||--o{ HOME_VISITS : "conducts"
    CITIZENS ||--o{ REFERRALS : "referred"
    VOLUNTEERS ||--o{ REFERRALS : "initiates"
```
