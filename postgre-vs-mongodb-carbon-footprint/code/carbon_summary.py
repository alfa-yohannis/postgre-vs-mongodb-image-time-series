import csv
from pathlib import Path

def main():
    emissions_file = Path("emissions.csv")
    output_markdown = Path("carbon_results.md")

    if not emissions_file.exists():
        print(f"Error: {emissions_file} not found.")
        return

    data = {}
    with emissions_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            project_name = row.get("project_name")
            if project_name:
                data[project_name] = row

    if not data:
        print("No emission data found.")
        return

    mongo_data = data.get("mongodb_phase", {})
    pg_data = data.get("postgres_phase", {})

    def format_float(val_str):
        if not val_str:
            return "N/A"
        try:
            return f"{float(val_str):.6f}"
        except:
            return val_str

    md_content = "# Carbon Footprint Measurement Results\n\n"
    md_content += "This report compares the energy consumption and CO₂ emissions of MongoDB and PostgreSQL benchmark phases.\n\n"
    md_content += "| Metric | MongoDB Phase | PostgreSQL Phase |\n"
    md_content += "| --- | --- | --- |\n"
    
    metrics = [
        ("Duration (s)", "duration"),
        ("Energy Consumed (kWh)", "energy_consumed"),
        ("CPU Energy (kWh)", "cpu_energy"),
        ("GPU Energy (kWh)", "gpu_energy"),
        ("RAM Energy (kWh)", "ram_energy"),
        ("Emissions (kg CO₂ eq)", "emissions"),
        ("Emissions Rate (kg CO₂ eq / s)", "emissions_rate")
    ]

    for label, key in metrics:
        m_val = format_float(mongo_data.get(key))
        p_val = format_float(pg_data.get(key))
        md_content += f"| {label} | {m_val} | {p_val} |\n"

    md_content += "\n## Summary Information\n"
    if mongo_data and pg_data:
        m_energy = float(mongo_data.get("energy_consumed", 0))
        p_energy = float(pg_data.get("energy_consumed", 0))
        if p_energy > 0 and m_energy > 0:
            diff_energy = ((m_energy - p_energy) / p_energy) * 100
            md_content += f"- **MongoDB Energy compared to PostgreSQL**: {diff_energy:+.2f}%\n"
            
        m_emissions = float(mongo_data.get("emissions", 0))
        p_emissions = float(pg_data.get("emissions", 0))
        if p_emissions > 0 and m_emissions > 0:
            diff_emis = ((m_emissions - p_emissions) / p_emissions) * 100
            md_content += f"- **MongoDB Emissions compared to PostgreSQL**: {diff_emis:+.2f}%\n"

    output_markdown.write_text(md_content, encoding="utf-8")
    print(f"Carbon summary successfully written to {output_markdown}")

if __name__ == "__main__":
    main()
