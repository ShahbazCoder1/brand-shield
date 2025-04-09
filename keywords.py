import os
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env
load_dotenv()
api_token = os.environ.get("GITHUB_TOKEN")

# Initialize OpenAI
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=api_token,
)

file_names = ["priority_1.txt", "priority_2.txt"]
all_keywords = []

# Step 1: Extract keywords and overwrite original files
for file_name in file_names:
    if not os.path.exists(file_name):
        print(f"❌ File not found: {file_name}")
        continue

    with open(file_name, "r", encoding="utf-8") as f:
        content = f.read()

    prompt = (
        "Only extract keywords, line by line. "
        "Return only keywords, line by line, in the same order.\n\n"
        + content
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You extract only keywords from each line."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=2048,
        top_p=1
    )

    keywords = response.choices[0].message.content.strip()
    all_keywords.append(keywords)

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(keywords + "\n")

# Step 2: Generate brand names without numbering or extra text
combined_keywords = "\n".join(all_keywords)
brand_prompt = (
    "Based on the following keywords, generate 10 unique and creative brand name ideas. "
    "Only return the brand names, one per line, no numbering or extra information.\n\n"
    + combined_keywords
)

brand_response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a branding expert."},
        {"role": "user", "content": brand_prompt}
    ],
    temperature=0.9,
    max_tokens=512,
    top_p=1
)

brand_names = brand_response.choices[0].message.content.strip()

# Save clean brand names
with open("potential_brands.txt", "w", encoding="utf-8") as f:
    f.write(brand_names + "\n")

print("✅ Clean brand names saved to: potential_brands.txt")
