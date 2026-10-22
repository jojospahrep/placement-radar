"""Employers tracked, keyed by the public job-board API they publish on.

To add an employer: find its careers site, check which ATS it uses (the job URL usually says:
myworkdayjobs.com, boards.greenhouse.io, jobs.lever.co, jobs.ashbyhq.com, jobs.smartrecruiters.com),
then add a row here and run `python -m radar probe` to confirm it answers.
"""

# Workday: (display name, sector, tenant, site, wd-host)
WORKDAY = [
    ("Rolls-Royce", "Aerospace & Defence", "rollsroyce", "professional", "wd3"),
    ("GE Aerospace", "Aerospace & Defence", "geaerospace", "GE_ExternalSite", "wd5"),
    ("Thales", "Aerospace & Defence", "thales", "Careers", "wd3"),
    ("Boeing", "Aerospace & Defence", "boeing", "EXTERNAL_CAREERS", "wd1"),
    ("KBR", "Aerospace & Defence", "kbr", "kbr_Careers", "wd5"),
    ("Dyson", "Consumer Products", "dyson", "dyson_Careers", "wd3"),
    ("Unilever", "Consumer Products", "unilever", "Unilever_Experienced_Professionals", "wd3"),
    ("3M", "Consumer Products", "3m", "Search", "wd1"),
    ("Renishaw", "Precision & Manufacturing", "renishaw", "Renishaw", "wd3"),
    ("Caterpillar", "Automotive & Off-highway", "cat", "CaterpillarCareers", "wd5"),
    ("Stellantis", "Automotive & Off-highway", "stellantis", "External_Career_Site_ID01", "wd3"),
    ("ABB", "Energy & Industrial", "abb", "External_Career_Page", "wd3"),
    ("Hitachi", "Energy & Industrial", "hitachi", "hitachi", "wd1"),
    ("Rockwell Automation", "Energy & Industrial", "rockwellautomation", "External_Rockwell_Automation", "wd1"),
    ("Johnson Controls", "Energy & Industrial", "jci", "jci", "wd5"),
    ("Carrier", "Energy & Industrial", "carrier", "Jobs", "wd5"),
    ("Baker Hughes", "Energy & Industrial", "bakerhughes", "bakerhughes", "wd5"),
    ("Shell", "Energy & Industrial", "shell", "ShellCareers", "wd3"),
    ("Centrica", "Energy & Industrial", "centrica", "centrica", "wd3"),
    ("Iberdrola / ScottishPower", "Energy & Industrial", "iberdrola", "iberdrola", "wd3"),
    ("Chevron", "Energy & Industrial", "chevron", "Jobs", "wd5"),
    ("GSK", "Pharma & Chemicals", "gsk", "GSKCareers", "wd5"),
    ("AstraZeneca", "Pharma & Chemicals", "astrazeneca", "Careers", "wd3"),
    ("Pfizer", "Pharma & Chemicals", "pfizer", "pfizerCareers", "wd1"),
    ("Novartis", "Pharma & Chemicals", "novartis", "novartis_Careers", "wd3"),
    ("Sanofi", "Pharma & Chemicals", "sanofi", "sanofiCareers", "wd3"),
    ("DuPont", "Pharma & Chemicals", "dupont", "Jobs", "wd5"),
    ("Smith+Nephew", "Medtech", "smithnephew", "External", "wd5"),
    ("Medtronic", "Medtech", "medtronic", "MedtronicCareers", "wd1"),
    ("Stryker", "Medtech", "stryker", "StrykerCareers", "wd1"),
    ("Johnson & Johnson", "Medtech", "jj", "JJ", "wd5"),
    ("Philips", "Medtech", "philips", "jobs-and-careers", "wd3"),
    ("NVIDIA", "Semiconductors & Compute", "nvidia", "NVIDIAExternalCareerSite", "wd5"),
    ("Intel", "Semiconductors & Compute", "intel", "External", "wd1"),
    ("Analog Devices", "Semiconductors & Compute", "analogdevices", "External", "wd1"),
    ("NXP", "Semiconductors & Compute", "nxp", "careers", "wd3"),
    ("Cadence", "Semiconductors & Compute", "cadence", "External_Careers", "wd1"),
    ("Applied Materials", "Semiconductors & Compute", "amat", "External", "wd1"),
    ("KLA", "Semiconductors & Compute", "kla", "Search", "wd1"),
    ("Micron", "Semiconductors & Compute", "micron", "External", "wd1"),
    ("Marvell", "Semiconductors & Compute", "marvell", "MarvellCareers", "wd1"),
    ("Broadcom", "Semiconductors & Compute", "broadcom", "External_Career", "wd1"),
    ("GlobalFoundries", "Semiconductors & Compute", "globalfoundries", "External", "wd1"),
    ("Samsung", "Semiconductors & Compute", "sec", "Samsung_Careers", "wd3"),
    ("Lumentum", "Semiconductors & Compute", "lumentum", "LITE", "wd5"),
    ("HPE", "Semiconductors & Compute", "hpe", "Jobsathpe", "wd5"),
    ("Motorola Solutions", "Semiconductors & Compute", "motorolasolutions", "Careers", "wd5"),
    ("Sky", "Telecoms & Media", "sky", "sky_Careers", "wd3"),
]

# Greenhouse: (display name, sector, board token)
GREENHOUSE = [
    ("Graphcore", "Semiconductors & Compute", "graphcore"),
    ("Fractile", "Semiconductors & Compute", "fractile"),
    ("Tenstorrent", "Semiconductors & Compute", "tenstorrent"),
    ("Lightmatter", "Semiconductors & Compute", "lightmatter"),
    ("Astera Labs", "Semiconductors & Compute", "asteralabs"),
    ("PsiQuantum", "Quantum & Deep Tech", "psiquantum"),
    ("Riverlane", "Quantum & Deep Tech", "riverlane"),
    ("Dexory", "Robotics & Autonomy", "dexory"),
    ("Figure", "Robotics & Autonomy", "figure"),
    ("Apptronik", "Robotics & Autonomy", "apptronik"),
    ("Agility Robotics", "Robotics & Autonomy", "agilityrobotics"),
    ("Waymo", "Robotics & Autonomy", "waymo"),
    ("Nuro", "Robotics & Autonomy", "nuro"),
    ("Kodiak", "Robotics & Autonomy", "kodiak"),
    ("Zipline", "Robotics & Autonomy", "flyzipline"),
    ("Helsing", "Aerospace & Defence", "helsing"),
    ("Isar Aerospace", "Aerospace & Defence", "isaraerospace"),
    ("Spire Global", "Aerospace & Defence", "spire"),
    ("Formlabs", "Precision & Manufacturing", "formlabs"),
    ("Nothing", "Consumer Products", "nothing"),
    ("Neuralink", "Medtech", "neuralink"),
    ("OVO Energy", "Energy & Industrial", "ovoenergy"),
    ("Monzo", "Software & Fintech", "monzo"),
]

# Ashby: (display name, sector, board name)
ASHBY = [
    ("Wayve", "Robotics & Autonomy", "wayve"),
    ("Oxa", "Robotics & Autonomy", "oxa"),
    ("Humanoid", "Robotics & Autonomy", "humanoid"),
    ("Skydio", "Robotics & Autonomy", "skydio"),
    ("Lightsource bp", "Energy & Industrial", "lightsource"),
    ("Enpal", "Energy & Industrial", "enpal"),
]

# Lever: (display name, sector, company slug)
LEVER = [
    ("Shield AI", "Aerospace & Defence", "shieldai"),
]

# SmartRecruiters: (display name, sector, company id). Queried with country=gb.
SMARTRECRUITERS = [
    ("Bosch", "Automotive & Off-highway", "BoschGroup"),
    ("Continental", "Automotive & Off-highway", "Continental"),
    ("Wabtec", "Energy & Industrial", "Wabtec"),
    ("Rotork", "Energy & Industrial", "Rotork"),
]
