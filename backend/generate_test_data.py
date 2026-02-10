"""
Generate synthetic customer test data for Unify.
Creates two CSV files with overlapping records (some duplicates with variations).
"""

import csv
import random
import os


# Base customer records
BASE_CUSTOMERS = [
    {
        "company_name": "Acme Corporation",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@acme.com",
        "phone": "+1-555-0101",
        "address_line1": "123 Main Street",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA",
        "tax_id": "12-3456789",
        "website": "https://www.acme.com",
    },
    {
        "company_name": "TechVentures Inc",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "email": "s.johnson@techventures.io",
        "phone": "+1-555-0202",
        "address_line1": "456 Innovation Drive",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94105",
        "country": "USA",
        "tax_id": "98-7654321",
        "website": "https://techventures.io",
    },
    {
        "company_name": "Global Solutions BV",
        "first_name": "Erik",
        "last_name": "van der Berg",
        "email": "erik@globalsolutions.nl",
        "phone": "+31-20-555-0303",
        "address_line1": "Keizersgracht 123",
        "city": "Amsterdam",
        "state": "North Holland",
        "postal_code": "1015 AA",
        "country": "Netherlands",
        "tax_id": "NL123456789B01",
        "website": "https://www.globalsolutions.nl",
    },
    {
        "company_name": "DataFlow Systems",
        "first_name": "Maria",
        "last_name": "Garcia",
        "email": "maria.garcia@dataflow.com",
        "phone": "+1-555-0404",
        "address_line1": "789 Tech Park Blvd",
        "city": "Austin",
        "state": "TX",
        "postal_code": "73301",
        "country": "USA",
        "tax_id": "45-6789012",
        "website": "https://dataflow.com",
    },
    {
        "company_name": "Nordic Consulting AS",
        "first_name": "Lars",
        "last_name": "Andersen",
        "email": "lars.andersen@nordic-consulting.no",
        "phone": "+47-22-555-0505",
        "address_line1": "Storgata 45",
        "city": "Oslo",
        "state": "Oslo",
        "postal_code": "0155",
        "country": "Norway",
        "tax_id": "NO987654321MVA",
        "website": "https://nordic-consulting.no",
    },
    {
        "company_name": "Bright Industries Ltd",
        "first_name": "James",
        "last_name": "Wilson",
        "email": "j.wilson@brightindustries.co.uk",
        "phone": "+44-20-555-0606",
        "address_line1": "10 Downing Lane",
        "city": "London",
        "state": "Greater London",
        "postal_code": "EC1A 1BB",
        "country": "United Kingdom",
        "tax_id": "GB123456789",
        "website": "https://www.brightindustries.co.uk",
    },
    {
        "company_name": "Summit Partners",
        "first_name": "Emily",
        "last_name": "Chen",
        "email": "emily.chen@summitpartners.com",
        "phone": "+1-555-0707",
        "address_line1": "300 Summit Avenue",
        "city": "Boston",
        "state": "MA",
        "postal_code": "02108",
        "country": "USA",
        "tax_id": "67-8901234",
        "website": "https://summitpartners.com",
    },
    {
        "company_name": "AlphaWorks GmbH",
        "first_name": "Klaus",
        "last_name": "Mueller",
        "email": "k.mueller@alphaworks.de",
        "phone": "+49-30-555-0808",
        "address_line1": "Friedrichstrasse 100",
        "city": "Berlin",
        "state": "Berlin",
        "postal_code": "10117",
        "country": "Germany",
        "tax_id": "DE123456789",
        "website": "https://alphaworks.de",
    },
]

# Unique records only in source A
UNIQUE_A = [
    {
        "company_name": "Pacific Rim Trading",
        "first_name": "Yuki",
        "last_name": "Tanaka",
        "email": "yuki@pacificrim.co.jp",
        "phone": "+81-3-555-0909",
        "address_line1": "1-2-3 Shibuya",
        "city": "Tokyo",
        "state": "Tokyo",
        "postal_code": "150-0002",
        "country": "Japan",
        "tax_id": "JP1234567890",
        "website": "https://pacificrim.co.jp",
    },
    {
        "company_name": "Maple Leaf Services",
        "first_name": "Claire",
        "last_name": "Tremblay",
        "email": "claire@mapleleaf.ca",
        "phone": "+1-416-555-1010",
        "address_line1": "200 Bay Street",
        "city": "Toronto",
        "state": "ON",
        "postal_code": "M5J 2J5",
        "country": "Canada",
        "tax_id": "CA123456789",
        "website": "https://mapleleaf.ca",
    },
]

# Unique records only in source B
UNIQUE_B = [
    {
        "company_name": "Outback Solutions Pty Ltd",
        "first_name": "Jack",
        "last_name": "Roberts",
        "email": "jack@outbacksolutions.com.au",
        "phone": "+61-2-555-1111",
        "address_line1": "50 George Street",
        "city": "Sydney",
        "state": "NSW",
        "postal_code": "2000",
        "country": "Australia",
        "tax_id": "AU12345678901",
        "website": "https://outbacksolutions.com.au",
    },
    {
        "company_name": "Sahara Logistics",
        "first_name": "Ahmed",
        "last_name": "Hassan",
        "email": "ahmed@saharalogistics.ae",
        "phone": "+971-4-555-1212",
        "address_line1": "Sheikh Zayed Road, Tower 3",
        "city": "Dubai",
        "state": "Dubai",
        "postal_code": "12345",
        "country": "UAE",
        "tax_id": "AE100123456",
        "website": "https://saharalogistics.ae",
    },
]


def create_variation(record: dict) -> dict:
    """Create a slightly different version of a record (simulating data from another system)."""
    varied = record.copy()
    variations = random.sample(range(7), k=random.randint(1, 3))

    for v in variations:
        if v == 0 and varied.get("company_name"):
            # Company name variation
            name = varied["company_name"]
            options = [
                name.upper(),
                name.replace("Inc", "Incorporated").replace("Ltd", "Limited").replace("BV", "B.V."),
                name + " ",  # trailing space
                name.replace(" ", "  "),  # double space
            ]
            varied["company_name"] = random.choice(options)
        elif v == 1 and varied.get("phone"):
            # Phone format variation
            phone = varied["phone"]
            varied["phone"] = phone.replace("-", " ").replace("+", "00")
        elif v == 2 and varied.get("address_line1"):
            # Address variation
            addr = varied["address_line1"]
            varied["address_line1"] = addr.replace("Street", "St.").replace("Drive", "Dr.").replace("Avenue", "Ave.")
        elif v == 3 and varied.get("first_name"):
            # First name typo
            name = varied["first_name"]
            if len(name) > 3:
                i = random.randint(1, len(name) - 2)
                varied["first_name"] = name[:i] + name[i + 1:]  # delete a char
        elif v == 4 and varied.get("website"):
            # Website variation
            web = varied["website"]
            varied["website"] = web.replace("https://www.", "http://").replace("https://", "")
        elif v == 5 and varied.get("postal_code"):
            # Postal code variation (add/remove space)
            pc = varied["postal_code"]
            if " " in pc:
                varied["postal_code"] = pc.replace(" ", "")
            else:
                mid = len(pc) // 2
                varied["postal_code"] = pc[:mid] + " " + pc[mid:]
        elif v == 6:
            # Missing field
            removable = [k for k in ["address_line1", "phone", "website"] if varied.get(k)]
            if removable:
                varied[random.choice(removable)] = ""

    return varied


def generate_source_a():
    """Generate source A: base records + unique A records."""
    records = []
    for rec in BASE_CUSTOMERS:
        records.append(rec.copy())
    for rec in UNIQUE_A:
        records.append(rec.copy())
    random.shuffle(records)
    return records


def generate_source_b():
    """Generate source B: varied versions of base records + unique B records."""
    records = []
    for rec in BASE_CUSTOMERS:
        records.append(create_variation(rec))
    for rec in UNIQUE_B:
        records.append(rec.copy())
    random.shuffle(records)
    return records


def write_csv(records: list, filepath: str, column_names: list):
    """Write records to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=column_names)
        writer.writeheader()
        for rec in records:
            # Ensure all fields exist
            row = {col: rec.get(col, "") for col in column_names}
            writer.writerow(row)


def main():
    """Generate test data files."""
    random.seed(42)

    columns = [
        "company_name", "first_name", "last_name", "email", "phone",
        "address_line1", "city", "state", "postal_code", "country",
        "tax_id", "website",
    ]

    # Source A uses standard column names
    source_a = generate_source_a()
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    write_csv(source_a, os.path.join(data_dir, "source_a_crm.csv"), columns)
    print(f"Generated source_a_crm.csv with {len(source_a)} records")

    # Source B uses different column names (simulating a different system)
    source_b = generate_source_b()
    b_columns = [
        "Company", "First Name", "Last Name", "E-mail", "Telephone",
        "Street Address", "City", "State/Province", "ZIP", "Country",
        "VAT Number", "Website URL",
    ]
    # Rename columns for source B
    b_records = []
    col_map = dict(zip(columns, b_columns))
    for rec in source_b:
        b_rec = {}
        for old_col, new_col in col_map.items():
            b_rec[new_col] = rec.get(old_col, "")
        b_records.append(b_rec)

    write_csv(b_records, os.path.join(data_dir, "source_b_erp.csv"), b_columns)
    print(f"Generated source_b_erp.csv with {len(source_b)} records")


if __name__ == "__main__":
    main()
