

# Set up the Gemini API key


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

    # 1. Load Requirements
    try:
        with open(requirements_file, 'r') as f:
            project_requirements = f.read()
    except FileNotFoundError:
        print(f"Error: Requirements file not found: {requirements_file}")
        return None
    except Exception as e:
        print(f"Error reading requirements file: {e}")
        return None

    # 2. Load Template and Convert to String Representation
    try:
        with open(template_file, 'r') as f:
            template_dict = yaml.safe_load(f)
            # Convert the template to a string *with placeholders*
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


    # 3. Construct the Prompt
    
    prompt = f"""
    You are a rtl design engineer.  I will provide project requirements and a YAML template 
    for a project specification. Your task is to fill in the YAML template based on 
    the project requirements.

    Project Requirements:
    ```
    {project_requirements}
    ```

    YAML Template:
    ```yaml
    {template_string}
    ```

    Instructions:
    - Carefully analyze the project requirements.
    - Do not include any markdown formatting, especially backticks (`) or triple backticks (```).  Output pure YAML only.
    - Fill in *all* placeholders in the YAML template with appropriate values derived 
      from the requirements.
    - Maintain the YAML structure exactly as provided in the template.  Do *not* add 
      or remove any fields. Only fill in the existing placeholders.
    - Use appropriate data types (e.g., strings, lists, dictionaries) as indicated by the template.
    - Ensure placeholders are filled with detailed and meaningful information. 
  If a placeholder cannot be determined from the given requirements, use "N/A" 
  or an empty list/dictionary as appropriate. Do *not* leave placeholders blank.
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
            raise ValueError("Generated output is not a dictionary.")

        # Validate against the template structure:
        def validate_structure(template, generated):
            for key, value in template.items():
                if key not in generated:
                    raise ValueError(f"Key '{key}' missing in generated output.")
                if isinstance(value, dict):
                    if not isinstance(generated[key], dict):
                        raise ValueError(f"Key '{key}' should be a dictionary.")
                    validate_structure(value, generated[key])
                elif isinstance(value, list):
                    if not isinstance(generated[key], list):
                        raise ValueError(f"Key '{key}' should be a list.")
                    #If the template shows an example list item, recursively check
                    if value and isinstance(value[0], dict):
                         for item in generated[key]:
                            validate_structure(value[0],item)


        validate_structure(template_dict, filled_spec)
        return filled_spec


    except (yaml.YAMLError, ValueError) as e:
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
The project is to design a simple counter.
The counter should be 8 bits wide.
It should have an enable signal.
It should have a synchronous reset.
It should count up.
        """)
    with open(template_file, "w") as f:
        f.write("""
module_name: ""  # Placeholder for the module name
description: ""  # Placeholder for a brief description
inputs:
  - name: ""    # Placeholder for input signal name
    width: ""   # Placeholder for input signal width
    description: "" # Placeholder for input signal description
  - name: ""
    width: ""
    description: ""
outputs:
  - name: ""    # Placeholder for output signal name
    width: ""   # Placeholder for output signal width
    description: "" # Placeholder for output signal description
parameters:
  - name: ""    # Placeholder for parameter name
    value: ""   # Placeholder for parameter value
    description: "" # Placeholder for parameter description
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
