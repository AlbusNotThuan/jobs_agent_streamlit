## Database Schema

You have access to a PostgreSQL database containing job market data. Use the following schema to understand the data structure and construct your SQL queries.

---

### **Table: `company`**
Stores information about unique companies.

| Column | Type | Description |
| :--- | :--- | :--- |
| `company_id` | `SERIAL` | **Primary Key.** A unique, auto-incrementing integer for each company. |
| `company_name` | `VARCHAR` | The name of the company. |
| `company_description`| `TEXT` | A description of the company, its industry, and culture. |

---

### **Table: `job`**
The central table containing detailed information for each job posting.

| Column | Type | Description |
| :--- | :--- | :--- |
| `job_id` | `VARCHAR` | **Primary Key.** A unique hash value identifying each job posting. |
| `company_id`| `INT` | **Foreign Key.** Links to `company.company_id`. |
| `job_title` | `VARCHAR` | The **raw, unstructured job title** as seen on the original posting. This is unreliable for categorization. |
| `job_expertise` | `VARCHAR` | A **standardized, structured job title** (e.g., "Data Engineer", "Frontend Developer"). **Use this column for analysis and filtering by job role.** |
| `yoe` | `INT` | The required "Years of Experience" as a label. These label are: "Internship", "Fresher Level", "Junior Level", "Associate Level", "Senior Level", "Director" and "Executive". If the question is about senority of a job, use this column |
| `salary` | `VARCHAR` | The salary information, stored as text (e.g., "Up to 2000 USD"). |
| `location` | `VARCHAR` | The geographical location of the job (e.g., "Ho Chi Minh City"). |
| `posted_date` | `TIMESTAMP` | The date and time the job was posted. |
| `requirements`| `TEXT` | The raw text describing the job requirements. |
| `description` | `TEXT` | The raw text describing the job responsibilities and duties. |
| `requirements_embedding`| `vector` | An embedding vector representing the semantic meaning of the `requirements` text. |
| `description_embedding`| `vector` | An embedding vector representing the semantic meaning of the `description` text. |

---

### **Table: `skill`**
A master list of all unique skills found in the job market.

| Column | Type | Description |
| :--- | :--- | :--- |
| `skill_id` | `SERIAL` | **Primary Key.** A unique, auto-incrementing integer for each skill. |
| `name` | `VARCHAR` | The name of the skill (e.g., "Python", "SQL", "AWS"). |
| `description`| `TEXT` | A brief description of the skill. |
| `embedding` | `vector` | An embedding vector representing the semantic meaning of the skill itself. |

---

### **Table: `job_skill`**
A join table that links jobs to skills, representing a many-to-many relationship. This table is automatically populated.

| Column | Type | Description |
| :--- | :--- | :--- |
| `job_id` | `VARCHAR` | **Composite Primary Key & Foreign Key.** Links to `job.job_id`. |
| `skill_id` | `INT` | **Composite Primary Key & Foreign Key.** Links to `skill.skill_id`. |
| `similarity` | `FLOAT` | A score from 0.0 to 1.0 indicating the cosine similarity between a job's requirements and a skill's embedding. A higher score means the skill is more relevant to the job. |