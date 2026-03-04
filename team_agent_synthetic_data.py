"""
TeamAgent Enterprise Graph Mock Data Generator
===========================================
This script generates a highly realistic, interconnected dataset for the TeamAgentGraph 
Spanner schema. It builds 1,000+ nodes (Persons, Skills, Companies, etc.) and thousands 
of complex edges (WorkedAt, HasSkill, ProfessionalConnection).

Unique Testing Scenarios Supported by this Data:
------------------------------------------------
1. Human-in-the-Loop Disambiguation: Includes multiple employees named "Alice Smith" 
   in different offices to intentionally trigger tie-breaking logic in the ULT.
2. Multi-Hop Graph Traversal: Hardcodes a deterministic org chart (Alice -> Diana -> Charles) 
   to test deep graph relationship queries (e.g., "Who is Alice's manager's manager?").
3. Semantic Vector Search: Bypasses standard 'Lorem Ipsum' by injecting real tech keywords 
   (GenAI, Spanner) and real companies/universities into bios to properly test vector similarity.
4. Alias Resolution: Seeds a user named "William" whose preferred name is "Bill" to test 
   exact-match name fallbacks.
5. Strict Edge Filtering: Enforces exactly one 'Primary' manager and EA per person to 
   validate specific GQL edge filters (e.g., isPrimary = True).
"""

import os
import random
import uuid
import logging
from datetime import datetime, timedelta
from faker import Faker
from google.cloud import spanner

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

# Configuration
NUM_PERSONS = 1000
NUM_SKILLS = 20
NUM_COMPANIES = 25
NUM_INSTITUTIONS = 75
NUM_LANGUAGES = 15
NUM_CERTS = 20

# Standardized Offices for POC
OFFICES = [
    {"location": "Pasadena", "code": "OFF_PAS_911", "state": "CA"},
    {"location": "Seattle", "code": "OFF_SEA_222", "state": "WA"},
    {"location": "New York", "code": "OFF_NY_333", "state": "NY"},
    {"location": "London", "code": "OFF_LON_444", "state": "UK"},
    {"location": "Chicago", "code": "OFF_CHI_555", "state": "IL"}
]

# Tech Keywords for Semantic Vector Testing
TECH_KEYWORDS = ["Google Cloud Spanner", "Vertex AI", "Generative AI", "React", "Python", 
                 "Machine Learning", "Graph Databases", "LangGraph", "Data Engineering", "LLMs"]

# Real-world recognizable entities for Vector/Semantic grouping tests
REAL_COMPANIES = ["Google", "Microsoft", "Amazon", "Accenture", "Deloitte", "Goldman Sachs"]
REAL_INSTITUTIONS = ["Stanford University", "MIT", "Harvard University", "UC Berkeley", "Oxford University"]

# ==========================================
# 1. GENERATE REFERENCE NODES
# ==========================================
def generate_reference_nodes():
    logger.info("Generating Reference Nodes...")
    
    skills = [{"skillCode": f"SK_{i}", "skillName": kw, "skillTypeCode": "TECH", "skillTypeName": "Technical"} 
              for i, kw in enumerate(TECH_KEYWORDS + [fake.catch_phrase() for _ in range(NUM_SKILLS - len(TECH_KEYWORDS))], 1)]
    
    companies = [{"companyName": comp} for comp in REAL_COMPANIES]
    companies += [{"companyName": f"{fake.company()} {fake.company_suffix()}"} for _ in range(NUM_COMPANIES - len(REAL_COMPANIES))]
    
    institutions = [{"institutionName": inst} for inst in REAL_INSTITUTIONS]
    institutions += [{"institutionName": f"{fake.city()} University"} for _ in range(NUM_INSTITUTIONS - len(REAL_INSTITUTIONS))]
    
    languages = [{"languageCode": f"L_{i}", "languageName": lang} for i, lang in enumerate(
        ["English", "Spanish", "French", "German", "Mandarin", "Japanese", "Korean", "Arabic", "Hindi", "Russian"], 1
    )]
    
    certs = [{"certId": f"CERT_{i}", "certName": f"Google Cloud Professional {kw}", "certTypeName": "Technical"} 
             for i, kw in enumerate(["Architect", "Data Engineer", "Machine Learning Engineer", "Developer"], 1)]
    
    for i in range(len(certs) + 1, NUM_CERTS + 1):
         certs.append({"certId": f"CERT_{i}", "certName": f"Certified {fake.job()}", "certTypeName": "Professional"})

    return skills, companies, institutions, languages, certs

# ==========================================
# 2. GENERATE PERSON NODES
# ==========================================
def generate_persons(num_persons):
    logger.info(f"Generating {num_persons} Person Nodes...")
    persons = []
    
    levels = ["Associate", "Senior Associate", "Manager", "Director", "Partner"]
    
    # INJECT DETERMINISTIC SEED DATA FOR POC TESTING
    seeded_data = [
        {"id": "PER_00001", "first": "Alice", "last": "Smith", "office": OFFICES[2], "level": "Senior Associate"}, # Alice NY
        {"id": "PER_00002", "first": "Alice", "last": "Smith", "office": OFFICES[3], "level": "Manager"}, # Alice LDN (Disambiguation)
        {"id": "PER_00003", "first": "Bob", "last": "Jones", "office": OFFICES[0], "level": "Associate"},   
        {"id": "PER_00004", "first": "Sarah", "last": "Connor", "office": OFFICES[0], "level": "Director"},
        {"id": "PER_00005", "first": "Dave", "last": "Williams", "office": OFFICES[1], "level": "Manager"},
        # New Seed: Org Chart Hierarchy testing
        {"id": "PER_00006", "first": "Diana", "last": "Director", "office": OFFICES[2], "level": "Director"},
        {"id": "PER_00007", "first": "Charles", "last": "CEO", "office": OFFICES[2], "level": "Partner"},
        # New Seed: Name Alias testing ("Bill" vs "William")
        {"id": "PER_00008", "first": "William", "pref": "Bill", "last": "Davis", "office": OFFICES[4], "level": "Manager"}
    ]

    for i in range(1, num_persons + 1):
        if i <= len(seeded_data):
            seed = seeded_data[i-1]
            first_name = seed["first"]
            pref_name = seed.get("pref", first_name)
            last_name = seed["last"]
            office = seed["office"]
            party_id = seed["id"]
            grade = seed["level"]
        else:
            first_name = fake.first_name()
            pref_name = first_name
            last_name = fake.last_name()
            office = random.choice(OFFICES)
            party_id = f"PER_{i:05d}"
            grade = random.choice(levels)
            
        tech_focus = random.sample(TECH_KEYWORDS, 2)
        bio = f"Experienced professional with a focus on {tech_focus[0]} and {tech_focus[1]}. {fake.sentence()}"
        
        person = {
            "partyId": party_id,
            "employeeId": f"WD_{fake.random_number(digits=6, fix_len=True)}",
            "microsoftId": f"{first_name.lower()}.{last_name.lower()}@mock-enterprise.com",
            "enterpriseGuid": str(uuid.uuid4()),
            "formattedName": f"{first_name} {last_name}",
            "preferredFirstName": pref_name,
            "lastName": last_name,
            "businessTitle": fake.job(),
            "globalGradeName": grade,
            "bioSummary": bio,
            "professionalInterestStatement": f"Interested in advancing my skills in {random.choice(TECH_KEYWORDS)}.",
            "cloudEmailAddress": f"{first_name.lower()}.{last_name.lower()}@cloud.mock.com",
            "phoneNumber": fake.phone_number(),
            "employmentStatusName": "Active",
            "contractTypeName": "Full-Time",
            "hireDate": fake.date_between(start_date='-10y', end_date='today').strftime('%Y%m%d'),
            "weeklyWorkingHours": 40.0,
            "workPercentage": 100.0,
            "waysofworking": random.choice(["Hybrid", "Virtual", "In-Office"]),
            "onshoreOffshoreIndicator": "Onshore",
            "legalEntityName": "Mock Enterprise LLC",
            "costCenter": f"CC_{random.randint(100, 999)}",
            "costCenterDescription": "Technology Operations",
            "globalLoSL1Name": "Advisory",
            "globalNetworkCompetencyName": "Engineering",
            "jobFamilyGroupName": "Technology",
            "jobFamilyName": "Engineering",
            "jobProfileCode": f"JP_{random.randint(10, 99)}",
            "jobProfileDescription": "Software Engineer",
            "industryCode": f"IND_{random.randint(1, 10)}",
            "industryName": random.choice(["Financial Services", "Healthcare", "Retail", "Tech"]),
            "countryCode": "USA" if office["state"] != "UK" else "GBR",
            "location": office["location"],
            "officeLocation": office["location"],
            "officeLocationCommonName": f"{office['location']} HQ",
            "officeLocationL2Description": "Main Hub",
            "officeLocationCode": office["code"],
            "state": office["state"],
            "accelerationCenterIdentifier": "AC_01",
            "accelerationCenterIndicator": "No",
            "localLoSL1": "Advisory",
            "localLoSL2": "Cloud & Digital",
            "localLoSL3": "Data & AI",
            "localLoSL4": "GenAI Solutions",
            "localLoSL5": "Engineering",
            "lastModified": datetime.utcnow().isoformat() + "Z",
            "longTermRelocationFlag": random.choice([True, False]),
            "shortTermRelocationFlag": random.choice([True, False]),
            "travelInterestFlag": random.choice([True, False]),
            "travelPercent": random.choice([0.0, 25.0, 50.0, 75.0]),
            "orgHierarchyDescription": f"Reports to {grade} of Engineering",
            "currentAreaOfFocus": tech_focus[0]
        }
        persons.append(person)
    return persons

# ==========================================
# 3. GENERATE EDGE RECORDS
# ==========================================
def generate_edges(persons, skills, companies, institutions, languages, certs):
    logger.info("Generating Edge Records...")
    
    has_skill = []
    worked_at = []
    prof_conn = []
    speaks = []
    alumnus_of = []
    recognized = []
    has_cert = []

    person_ids = [p["partyId"] for p in persons]
    conn_types = ['CAREER_COACH', 'MANAGER', 'EA', 'TC', 'DL', 'RL', 'DM']

    for p in persons:
        pid = p["partyId"]

        # 1. HasSkill
        p_skills = random.sample(skills, random.randint(2, 5))
        for sk in p_skills:
            has_skill.append({
                "partyId": pid,
                "skillCode": sk["skillCode"],
                "isTopSkill": random.choice([True, False]),
                "isDesiredSkill": random.choice([True, False]),
                "skillLevel": random.choice(["Beginner", "Intermediate", "Expert"])
            })

        # 2. WorkedAt
        p_comps = random.sample(companies, random.randint(2, 4))
        for comp in p_comps:
            start_date = fake.date_between(start_date='-15y', end_date='-5y')
            worked_at.append({
                "partyId": pid,
                "companyName": comp["companyName"],
                "jobTitle": fake.job(),
                "startDate": start_date.strftime('%Y-%m-%d'),
                "endDate": (start_date + timedelta(days=random.randint(365, 1000))).strftime('%Y-%m-%d'),
                "location": fake.city(),
                "experienceDescription": fake.catch_phrase()
            })

        # 3. ProfessionalConnection (Enforcing exact org hierarchy for seeds)
        has_primary = {c_type: False for c_type in conn_types}
        
        # Hardcode Org Chart: Alice -> Diana -> Charles
        if pid == "PER_00001":
            prof_conn.append({"subjectId": pid, "relatedPersonId": "PER_00006", "connectionType": "MANAGER", "isPrimary": True})
            has_primary["MANAGER"] = True
        elif pid == "PER_00006":
            prof_conn.append({"subjectId": pid, "relatedPersonId": "PER_00007", "connectionType": "MANAGER", "isPrimary": True})
            has_primary["MANAGER"] = True

        p_conns = random.sample([x for x in person_ids if x != pid and x not in ["PER_00006", "PER_00007"]], random.randint(3, 5))
        for i, conn_id in enumerate(p_conns):
            c_type = random.choice(['MANAGER', 'DM']) if i == 0 else random.choice(conn_types)
            
            # Enforce strict 'isPrimary' rules (Only 1 primary per type)
            is_prim = not has_primary[c_type]
            has_primary[c_type] = True
            
            prof_conn.append({
                "subjectId": pid,
                "relatedPersonId": conn_id,
                "connectionType": c_type,
                "isPrimary": is_prim
            })

        # 4. Speaks
        p_langs = random.sample(languages, random.randint(1, 3))
        for lang in p_langs:
            speaks.append({
                "partyId": pid,
                "languageCode": lang["languageCode"],
                "abilityTypeName": random.choice(["Reading", "Speaking", "Writing", "Overall"]),
                "proficiencyLevel": random.choice(["Native", "Fluent", "Conversational", "Basic"]),
                "lastAssessedDate": datetime.utcnow().isoformat() + "Z"
            })

        # 5. AlumnusOf
        p_insts = random.sample(institutions, random.randint(1, 2))
        for inst in p_insts:
            start_date = fake.date_between(start_date='-20y', end_date='-10y')
            alumnus_of.append({
                "partyId": pid,
                "institutionName": inst["institutionName"],
                "degreeName": random.choice(["B.S. Computer Science", "MBA", "M.S. Data Science", "B.A. Business"]),
                "completionDate": (start_date + timedelta(days=1460)).strftime('%Y-%m-%d'),
                "startDate": start_date.strftime('%Y-%m-%d')
            })

        # 6. Recognized
        p_recs = random.sample([x for x in person_ids if x != pid], random.randint(1, 3))
        for rec_id in p_recs:
            recognized.append({
                "nominatorId": pid,
                "nomineeId": rec_id,
                "nominationId": f"NOM_{str(uuid.uuid4())[:8]}",
                "dateNominated": datetime.utcnow().isoformat() + "Z",
                "reason": fake.sentence(),
                "criteria": "Outstanding Leadership",
                "pointsAwarded": random.randint(100, 1000),
                "spotBonusAmount": float(random.choice([0, 500, 1000, 2000]))
            })

        # 7. HasCertification
        p_certs = random.sample(certs, random.randint(1, 3))
        for crt in p_certs:
            issue = fake.date_between(start_date='-5y', end_date='today')
            has_cert.append({
                "partyId": pid,
                "certId": crt["certId"],
                "issueDate": issue.strftime('%Y-%m-%d'),
                "expirationDate": (issue + timedelta(days=1095)).strftime('%Y-%m-%d')
            })

    return has_skill, worked_at, prof_conn, speaks, alumnus_of, recognized, has_cert


# ==========================================
# 4. SPANNER BATCH INSERTION
# ==========================================
def insert_data_to_spanner(instance_id, database_id, nodes, edges):
    logger.info("Initializing Spanner Client...")
    spanner_client = spanner.Client()
    instance = spanner_client.instance(instance_id)
    database = instance.database(database_id)

    skills, companies, institutions, languages, certs, persons = nodes
    has_skill, worked_at, prof_conn, speaks, alumnus_of, recognized, has_cert = edges

    def insert_batch(transaction, table_name, data):
        if not data: return
        columns = list(data[0].keys())
        values = [[row[col] for col in columns] for row in data]
        
        # Spanner limits mutations per commit (20,000 cells max). We batch them.
        batch_size = 500
        for i in range(0, len(values), batch_size):
            transaction.insert_or_update(
                table=table_name,
                columns=columns,
                values=values[i:i+batch_size]
            )
            
    logger.info("Writing data to Spanner...")
    try:
        # Node insertions
        database.run_in_transaction(insert_batch, "Skill", skills)
        database.run_in_transaction(insert_batch, "Company", companies)
        database.run_in_transaction(insert_batch, "Institution", institutions)
        database.run_in_transaction(insert_batch, "Language", languages)
        database.run_in_transaction(insert_batch, "Certification", certs)
        database.run_in_transaction(insert_batch, "Person", persons)
        
        # Edge insertions
        database.run_in_transaction(insert_batch, "HasSkill", has_skill)
        database.run_in_transaction(insert_batch, "WorkedAt", worked_at)
        database.run_in_transaction(insert_batch, "ProfessionalConnection", prof_conn)
        database.run_in_transaction(insert_batch, "Speaks", speaks)
        database.run_in_transaction(insert_batch, "AlumnusOf", alumnus_of)
        database.run_in_transaction(insert_batch, "Recognized", recognized)
        database.run_in_transaction(insert_batch, "HasCertification", has_cert)
        
        logger.info("✅ All Data Successfully Inserted!")
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")

# ==========================================
# 5. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # Ensure you have set your GCP environment variables (e.g. GOOGLE_APPLICATION_CREDENTIALS)
    SPANNER_INSTANCE = os.getenv("SPANNER_INSTANCE", "your-spanner-instance")
    SPANNER_DATABASE = os.getenv("SPANNER_DATABASE", "your-database-id")

    # 1. Generate Nodes
    skills, companies, institutions, languages, certs = generate_reference_nodes()
    persons = generate_persons(NUM_PERSONS)
    
    # 2. Generate Edges
    edges = generate_edges(persons, skills, companies, institutions, languages, certs)
    
    # 3. Insert into DB
    nodes = (skills, companies, institutions, languages, certs, persons)
    
    # UNCOMMENT below line to actually push to Spanner:
    # insert_data_to_spanner(SPANNER_INSTANCE, SPANNER_DATABASE, nodes, edges)
    
    logger.info(f"Generated {len(persons)} Persons, {len(edges[2])} Professional Connections, and {len(edges[6])} Certification Edges.")
    logger.info("Script execution complete. Ready for Spanner ingestion.")
