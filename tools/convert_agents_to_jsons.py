import json
from typing import List, Dict, Any
# type: ignore

def parse_agent_list_md(md_content: str) -> List[Dict[str, Any]]:
    """
    Parses the 'Agents' table from the AgentList.md content.
    Assumes a Markdown table structure.
    """
    agents_data = []
    lines = md_content.splitlines()
    
    # Find the start of the agents table
    table_start_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('| Row '):
            table_start_index = i
            break
        if line.strip().startswith('|--'):
            table_start_index = i-1
            break

    if table_start_index == -1:
        print("Warning: Agents table not found in the Markdown content.")
        return []

    # Extract header
    header_line = lines[table_start_index] # Line after the header separator
    headers = [h.strip() for h in header_line.strip().split('|') if h.strip()]
    
    print( "\r\n\r\n" )
    print ("headers:\r\n")
    print (headers)
    print( "\r\n\r\n" )

    # Find the index of relevant columns, allowing for variations in naming
    col_indices = {}
    for i, header in enumerate(headers):
        if header.lower() == 'id': col_indices['id'] = i+1
        elif header.lower() == 'category': col_indices['category'] = i+1
        elif header.lower() == 'name': col_indices['name'] = i+1
        elif header.lower() == 'summary': col_indices['summary'] = i+1
        elif header.lower() == 'description': col_indices['description'] = i+1
        elif header.lower() == 'method': col_indices['method'] = i+1
        elif header.lower() == 'trigger': col_indices['trigger'] = i+1
        elif header.lower() == 'inputs': col_indices['inputs'] = i+1
        elif header.lower() == 'outputs': col_indices['outputs'] = i+1
        elif header.lower() == 'row': col_indices['row'] = i+1 # Added for row number if present
        
    print ("col_indices:\r\n")
    print (col_indices)
    print( "\r\n\r\n" )
    
    # Ensure essential headers are present
    if 'id' not in col_indices or 'name' not in col_indices or 'method' not in col_indices:
        print(f"Error: Essential columns (ID, Name, Method) not found in table headers: {headers}")
        return []

    # Process data rows
    for i in range(table_start_index + 2, len(lines)):
        line = lines[i].strip()
        if not line or line.startswith('|--'): # Skip empty lines or further separators
            continue
            
        cells = [cell.strip() for cell in line.split('|') if cell.strip() or '|' in line] # Split carefully, keeping empty cells if '|' is present
        # print( "cells: \r\n\r\n" )
        # print( cells )
        # print( "\r\n\r\n" )
        
        # Reconstruct cells if split was too aggressive due to markdown formatting, e.g., within descriptions
        # This is a simplification; robust markdown table parsing is complex.
        # For now, assume simple cell content.
        
        if len(cells) < len(headers):
             # Attempt to correct for potential issues with cell splitting (e.g., pipes in descriptions)
             # This is heuristic and might need adjustment based on actual markdown content.
             # A more robust approach would involve a proper markdown table parser library.
             print(f"Warning: Skipping potentially malformed row {i+1} due to cell count mismatch. Expected {len(headers)}, got {len(cells)}. Line: '{line}'")
             continue

        agent = {}
        # Assign values based on found column indices
        if 'row' in col_indices:
            agent['row'] = int(cells[col_indices['row']])
        else:
            agent['row'] = i - (table_start_index + 2) + 1 # Approximate row if not explicitly in table

        agent['id'] = int(cells[col_indices['id']]) if 'id' in col_indices else None
        agent['category'] = cells[col_indices['category']] if 'category' in col_indices else None
        agent['name'] = cells[col_indices['name']] if 'name' in col_indices else None
        agent['summary'] = cells[col_indices['summary']] if 'summary' in col_indices else None
        agent['description'] = cells[col_indices['description']] if 'description' in col_indices else None
        agent['method'] = cells[col_indices['method']] if 'method' in col_indices else None
        agent['trigger'] = cells[col_indices['trigger']] if 'trigger' in col_indices else None
        agent['inputs'] = cells[col_indices['inputs']] if 'inputs' in col_indices else None
        agent['outputs'] = cells[col_indices['outputs']] if 'outputs' in col_indices else None
        
        # Clean up None values if not explicitly found in the row
        for key in list(agent.keys()):
            if agent[key] is None and key in col_indices: # Only remove if column existed but was empty
                 agent[key] = "" # Set to empty string for consistency in JSON
            elif key not in col_indices: # If column header wasn't found at all
                 if key in ['row', 'id']: agent[key] = None # Keep row/id as None if not found
                 else: agent[key] = "" # Default to empty string for others


        agents_data.append(agent)
        
    return agents_data

def generate_agent_json_files(md_filepath: str, output_dir: str = "/mnt/data"):
    """
    Reads AgentList.md, parses it, and generates three structured JSON files.
    """
    try:
        with open(md_filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {md_filepath}")
        return
    except Exception as e:
        print(f"Error reading file {md_filepath}: {e}")
        return

    agents_list = parse_agent_list_md(md_content)

    if not agents_list:
        print("No agent data parsed. JSON files will not be generated.")
        return

    # --- Prepare data for different JSON structures ---

    # 1. agents_definitions.json
    definitions_data = []
    for agent in agents_list:
        definitions_data.append({
            "id": agent.get("id"),
            "name": agent.get("name"),
            "category": agent.get("category"),
            "summary": agent.get("summary"),
            "description": agent.get("description")
        })

    # 2. agents_triggers.json
    # This part is heuristic: trying to infer trigger from the 'trigger' column.
    # If 'trigger' column contains complex info, this needs more sophisticated parsing.
    triggers_data = []
    for agent in agents_list:
        trigger_info = agent.get("trigger", "").strip()
        # Basic assumption: if trigger_info is not empty, it's a trigger description.
        # More complex parsing might be needed if triggers have structured data (e.g., specific event names).
        triggers_data.append({
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
            "trigger_description": trigger_info if trigger_info else "N/A",
            # Add more structured trigger fields if 'trigger' column has them
            # e.g., "event_type": "on_new_content", "timing": "immediately"
        })

    # 3. agents_io_mapping.json
    # This requires mapping agent names/IDs to IO classes.
    # The 'inputs' and 'outputs' columns in MD are just strings;
    # we need to map them to actual class names in agent_io files.
    # This mapping needs to be curated or inferred.
    # For now, we'll store the string representation from MD.
    # A more advanced script would read agent_io/*.py files to establish this.
    io_mapping_data = []
    for agent in agents_list:
        input_str = agent.get("inputs", "").strip()
        output_str = agent.get("outputs", "").strip()
        
        # Basic parsing assuming comma-separated names or single name
        inputs = [inp.strip() for inp in input_str.split(',') if inp.strip()] if input_str else []
        outputs = [out.strip() for out in output_str.split(',') if out.strip()] if output_str else []

        io_mapping_data.append({
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
            "inputs": inputs, # Storing as strings from MD
            "outputs": outputs, # Storing as strings from MD
        })

    method_mapping_data = []
    for agent in agents_list:
        method_str = agent.get("method", "").strip()

        triggers_data.append({
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
            "method": method_str if method_str else "N/A",
        })

    # --- Save to JSON files ---
    files_to_save = {
        "agents_definitions.json": definitions_data,
        "agents_triggers.json": triggers_data,
        "agents_io_mapping.json": io_mapping_data,
        "agents_methods.json": method_mapping_data
    }

    for filename, data in files_to_save.items():
        filepath = f"{output_dir}/{filename}"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Successfully created {filepath}")
        except Exception as e:
            print(f"Error writing file {filepath}: {e}")

# --- Usage Example ---
# Assuming AgentList.md is available in the /mnt/data directory
# and you want the output JSON files to be saved there as well.

# Make sure 'edu_agent_system_v3.zip' is unzipped and AgentList.md is accessible.
# If AgentList.md is inside the zip, you'd need to extract it first or adjust the path.
# For this script, let's assume AgentList.md is directly accessible at '[/mnt/data/doc/AgentList.md'](https://storage.gapgpt.app/media/code_interpreter/e0ceda98-8611-417a-9ccb-88f4e264b469/AgentList.md%27)
# If it's at the root of the zip, use '[/mnt/data/AgentList.md'](https://storage.gapgpt.app/media/code_interpreter/e0ceda98-8611-417a-9ccb-88f4e264b469/AgentList.md%27)

# Example call:
# Assuming AgentList.md is at [/mnt/data/doc/AgentList.md](https://storage.gapgpt.app/media/code_interpreter/e0ceda98-8611-417a-9ccb-88f4e264b469/AgentList.md)
generate_agent_json_files('../doc/AgentList.md', '../config/models/agents_definition') 

# If AgentList.md was extracted to the root of /mnt/data:
# generate_agent_json_files('[/mnt/data/AgentList.md'](https://storage.gapgpt.app/media/code_interpreter/e0ceda98-8611-417a-9ccb-88f4e264b469/AgentList.md%27), '/mnt/data')
