from database import SessionLocal
from database import User
from database import Company

db = SessionLocal()

company = Company(
    company_name="Demo Company",
    plan="Professional"
)

db.add(company)

engineer = User(
    username="engineer1",
    name="Site Engineer",
    password="1234",
    role="engineer",
    company="Demo Company"
)

qa = User(
    username="qa1",
    name="QA Manager",
    password="1234",
    role="qa",
    company="Demo Company"
)

admin = User(
    username="admin",
    name="System Admin",
    password="1234",
    role="admin",
    company="Demo Company"
)

db.add(engineer)
db.add(qa)
db.add(admin)

db.commit()

print("Users Created")
