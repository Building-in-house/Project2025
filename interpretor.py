import google.generativeai as genai
import os
import yaml
from dotenv import load_dotenv

load_dotenv('project.env')

def generate_spec_from_files(requirements_file: str, template_file: str) -> dict:
    """Generates a project specification from a requirements file and a YAML template.

    Args:
        requirements_file: Path to the text file containing project requirements.
        template_file: Path to the YAML file defining the specification template.

    Returns:
        A dictionary representing the filled-in YAML specification, or None on error.
    """

    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.0-flash')

    try:
        with open(requirements_file, 'r') as f:
            project_requirements = f.read()
    except FileNotFoundError:
        print(f"Error: Requirements file not found: {requirements_file}")
        return None
    except Exception as e:
        print(f"Error reading requirements file: {e}")
        return None

    try:
        with open(template_file, 'r') as f:
            template_dict = yaml.safe_load(f)
            template_string = yaml.dump(template_dict)
    except FileNotFoundError:
        print(f"Error: Template file not found: {template_file}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML template: {e}")
        return None
    except Exception as e:
        print(f"Error reading template file: {e}")
        return None

    prompt = f"""
    You are a rtl design engineer.  I will provide project requirements and a YAML template 
    for a project specification. Your task is to fill in the YAML template based on 
    the project requirements.

    Project Requirements:
    ```
    {project_requirements}
    ```

    YAML Template:
    {template_string}


    Instructions:
    - Carefully analyze the project requirements.
    - Do not include any markdown formatting, especially backticks (`) or triple backticks (```).  Output pure YAML only.
    - Maintain the YAML structure exactly as provided in the template. Do *not* remove any fields.
    - Fill in the fields in the template in the order provided in the template file.
    - Fill in *all* placeholders in the YAML template with appropriate values derived from the requirements.
    - If a placeholder cannot be determined from the given requirements, use your rtl design engineering knowledge to fill the placeholders and also add necessary fields based on the requirements. 
    - if a placeholder is not applicable, remove it.
    - Use appropriate data types (e.g., strings, lists, dictionaries) as indicated by the template.
    - Ensure placeholders are filled with detailed and meaningful information. 
    - Be as detailed as possible in your descriptions.

    Filled-in YAML Specification:
    """
    # we don't want to remove any field s but add new fields based on user's requirements
    #in placeholder line we want the llm to be creative so we need to connect this with the hardware aware llm also we need hardware with this data also
       
    # 4. Call Gemini
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        print(f"Error generating content from Gemini: {e}")
        return None


    # 5. Parse the Response (and Validate)
    try:
        filled_spec = yaml.safe_load(response.text)
        
        # --- Validation (Crucial!) ---
        if not isinstance(filled_spec, dict):
             print("Generated output is not a dictionary.")

        # Validate against the template structure:
        def validate_structure(template, generated):
            for key, value in template.items():
                if key not in generated:
                     print(f"Key '{key}' missing in generated output.")
                if isinstance(value, dict):
                    if not isinstance(generated[key], dict):
                         print(f"Key '{key}' should be a dictionary.")
                    validate_structure(value, generated[key])
                elif isinstance(value, list):
                    if not isinstance(generated[key], list):
                         print(f"Key '{key}' should be a list.")
                    #If the template shows an example list item, recursively check
                    if value and isinstance(value[0], dict):
                         for item in generated[key]:
                            validate_structure(value[0],item)


        validate_structure(template_dict, filled_spec)
        return filled_spec


    except (yaml.YAMLError, print) as e:
        print(f"Error parsing or validating LLM output: {e}")
        print("---- Raw LLM Output ----")
        print(response.text)
        print("---- End Raw Output ----")
        return None
    
def main():
    """Main function to demonstrate the script's functionality."""

    # --- Example Usage (Replace with your actual files) ---
    requirements_file = "requirements.txt"  # Example requirements file
    template_file = "template.yaml"        # Example template file

    # Create dummy files for the example
    with open(requirements_file, "w") as f:
        f.write("""
        create a 8-bit calculator which can add and subtract two 8-bit numbers.it should use two 8-bit inputs and one 8-bit output.        
        """)
    with open(template_file, "w") as f:
        f.write("""
rtl_project:
  project_description: ""  # Placeholder for project description
  top_module: <top_module_name>  # Placeholder for top module name among module name key.
  module_list:
       <module_name_key>: <hdl_file_name>.<hdl_file_extension>#optional placeholders can be add as many based on number of modules. 
  module_functions:
    - module_name: <module_name_key>
      module_description: ""  # Placeholder for module description
      inputs:
        - net_name: ""  # Placeholder for input signal name
          width: ""  # Placeholder for input signal width
          depth: "" # Placeholder for input signal depth
          description: ""  # Placeholder for input signal description
      outputs:
        - name: ""  # Placeholder for output signal name
          width: ""  # Placeholder for output signal width
          depth: "" # Placeholder for output signal depth
          description: ""  # Placeholder for output signal description
      parameters:
        - name: ""  # Placeholder for parameter name
          value: ""  # Placeholder for parameter value
          description: ""  # Placeholder for parameter description
""")

    # --- Call the function and print the result ---
    filled_specification = generate_spec_from_files(requirements_file, template_file)

    if filled_specification:
        print("\nGenerated Specification:")
        print(yaml.dump(filled_specification))  # Pretty-print the YAML
    else:
        print("\nSpecification generation failed.")

    with open("spec.yaml", "w") as file:
        yaml.dump(filled_specification, file, sort_keys=False, indent=4)
    print("Specification saved to 'spec.yaml'.")

    # Clean up dummy files
    os.remove(requirements_file)
    os.remove(template_file)
if __name__ == "__main__":
    main()
