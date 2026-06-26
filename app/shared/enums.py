import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    PROVINCE_ADMIN = "province_admin"
    DISTRICT_ADMIN = "district_admin"
    SUBDISTRICT_ADMIN = "subdistrict_admin"
    VOLUNTEER = "volunteer"
    VIEWER = "viewer"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class VolunteerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class IncomeGroup(str, enum.Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HousingType(str, enum.Enum):
    OWN = "own"
    RENT = "rent"
    PUBLIC = "public"
    OTHER = "other"


class ReferralStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReferralTarget(str, enum.Enum):
    HOSPITAL = "hospital"
    HEALTH_CENTER = "health_center"
    MUNICIPALITY = "municipality"
    NGO = "ngo"


class VisitType(str, enum.Enum):
    ROUTINE = "routine"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    REFERRAL = "referral"
