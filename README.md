# Information Architecture V2.60
## MKI Community Health Platform

### Navigation Structure (8 Groups)

| Group | Icon | Purpose | Target Users |
|---|---|---|---|
| HOME | 🏠 | Daily workspace, tasks, notifications | All users |
| PEOPLE | 👥 | Population management, citizens, volunteers | All users |
| CARE | 🩺 | Care coordination, visits, referrals, assessments | All users |
| SERVICES | 🤝 | Community services, projects, campaigns | Officers+ |
| MAPS | 📍 | GIS intelligence, heatmaps, coverage | Officers+ |
| INSIGHTS | 📈 | Analytics, reports, scorecards | Officers+ |
| AI | 🧠 | AI assistant, summaries, analysis | All users |
| ADMIN | ⚙️ | System administration | Admins only |
| HELP | ❓ | User guide, FAQ, training | All users |

### Role Navigation Matrix

| Group | Super Admin | Province Admin | District Admin | Volunteer | Viewer |
|---|---|---|---|---|---|
| HOME | ✅ | ✅ | ✅ | ✅ | ✅ |
| PEOPLE | ✅ | ✅ | ✅ | ✅ | ✅ |
| CARE | ✅ | ✅ | ✅ | ✅ | — |
| SERVICES | ✅ | ✅ | ✅ | — | — |
| MAPS | ✅ | ✅ | ✅ | — | — |
| INSIGHTS | ✅ | ✅ | ✅ | — | ✅ |
| AI | ✅ | ✅ | ✅ | ✅ | — |
| ADMIN | ✅ | ✅ | — | — | — |
| HELP | ✅ | ✅ | ✅ | ✅ | ✅ |

### Design Principles
- **Workflow-centric**: Users think "I need to do X" not "Where is module Y"
- **Role-based**: Each role sees only relevant navigation
- **Context-aware**: Breadcrumbs always show current location
- **Discoverable**: Global search finds anything in <500ms
- **Enterprise**: Inspired by Microsoft Fabric, Salesforce Health Cloud
