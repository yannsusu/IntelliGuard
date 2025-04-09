import json

input_file = "../../Datasets/combined_data.jsonl"
output_file = "../../Datasets/matched_data.jsonl"

with open(input_file, "r", encoding="utf-8") as infile, \
        open(output_file, "w", encoding="utf-8") as outfile:
    for line in infile:
        data = json.loads(line)
        id = data.get("id", "")
        text = data.get("text", "")
        label = data.get("label", "")

        policies = data.get("policies", [])

        policies_data = []
        for policy in policies:
            policy_text = policy.get("text", "")

            policies_data.append({
                "policy_text": policy_text,
            })

        output_data = {
            "id": id,
            "text": text,
            "policies": policies_data,
            "label": label
        }

        outfile.write(json.dumps(output_data, ensure_ascii=False) + "\n")