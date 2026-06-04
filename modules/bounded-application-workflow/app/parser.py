from app.domain.models import JobDescription


def parse_job_description(raw_text: str) -> JobDescription:
    if not raw_text.strip():
        raise ValueError("Job description text cannot be empty.")

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    title = lines[0]

    company = None
    location = None
    seniority = None
    employment_type = None

    required_skills = []
    nice_to_have_skills = []

    for line in lines:
        lower = line.lower()

        if lower.startswith("company:"):
            company = line.split(":", 1)[1].strip()

        elif lower.startswith("location:"):
            location = line.split(":", 1)[1].strip()

        elif lower.startswith("seniority:"):
            seniority = line.split(":", 1)[1].strip()

        elif lower.startswith("employment type:"):
            employment_type = line.split(":", 1)[1].strip()

        elif line.startswith("-"):
            required_skills.append(line.lstrip("- ").strip())

        elif line.startswith("+"):
            nice_to_have_skills.append(line.lstrip("+ ").strip())

    return JobDescription(
        title=title,
        company=company,
        location=location,
        description=raw_text,
        required_skills=required_skills,
        nice_to_have_skills=nice_to_have_skills,
        seniority=seniority,
        employment_type=employment_type,
    )