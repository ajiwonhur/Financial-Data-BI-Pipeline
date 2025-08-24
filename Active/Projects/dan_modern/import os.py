import os
import json
import glob
import argparse  # Import the argparse module
import textwrap

from google import genai
from google.genai import types


def ensure_all_fields_present(data, schema):
    """
    Ensures that all fields defined in the schema are present in the data,
    setting missing fields to null, and maintains schema order.
    For object fields, ensures the entire object structure is present,
    with only leaf values potentially set to null.

    Args:
        data (dict): The parsed invoice data (potentially incomplete).
        schema (genai.types.Schema): The schema definition.

    Returns:
        dict: The data with all schema fields present in schema order
              (missing fields set to null, complete object structure ensured).
    """
    if not isinstance(data, dict): # Handle cases where data is not a dict at the top level, should initialize as dict.
        data = {}

    output_data = {} # Initialize a new dictionary to maintain schema order

    if schema.type == genai.types.Type.OBJECT and schema.properties:
        for prop_name, prop_schema in schema.properties.items():
            if prop_name in data:
                prop_value = data[prop_name]
                if prop_schema.type in [genai.types.Type.OBJECT, genai.types.Type.ARRAY]:
                    if isinstance(prop_value, dict):
                        output_data[prop_name] = ensure_all_fields_present(prop_value, prop_schema)
                    elif isinstance(prop_value, list) and prop_schema.items:
                        output_data[prop_name] = [ensure_all_fields_present(item, prop_schema.items) if isinstance(item, dict) else item for item in prop_value]
                    else: # if it's object/array in schema but not in data, still process as object/array for completeness
                        output_data[prop_name] = ensure_all_fields_present({}, prop_schema) if prop_schema.type == genai.types.Type.OBJECT else [] if prop_schema.type == genai.types.Type.ARRAY else None # Should ideally not reach here in normal cases
                else:
                    output_data[prop_name] = prop_value
            else:
                if prop_schema.type == genai.types.Type.OBJECT:
                    output_data[prop_name] = ensure_all_fields_present({}, prop_schema) # Ensure complete object structure even if top-level is missing
                elif prop_schema.type == genai.types.Type.ARRAY:
                    output_data[prop_name] = [] # Ensure empty array if array field is missing
                else:
                    output_data[prop_name] = None # Set missing leaf field to null

        return output_data # Return the new dictionary with schema order
    elif schema.type == genai.types.Type.ARRAY and schema.items:
        if isinstance(data, list):
            return [ensure_all_fields_present(item, schema.items) if isinstance(item, dict) else item for item in data]
        else:
            return [] # Return empty array if data is not a list but schema is array
    return data  # For primitive types, return as is


def parse_invoice(image_paths):
    """
    Parse all images of an invoice into a structured JSON, including verbatim OCR.

    Args:
        image_paths (list): List of paths to invoice images

    Returns:
        dict: Parsed invoice data including verbatim OCR
    """
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    if not image_paths:
        print("No image files provided")
        return None

    # Upload all files
    files = []
    for img_path in image_paths:
        try:
            files.append(client.files.upload(file=img_path))
        except Exception as e:
            print(f"Error uploading file {img_path}: {e}")
            return None # Stop processing if file upload fails


    model = "gemini-2.0-flash"

    # Create parts for each image
    parts = []
    for file in files:
        parts.append(
            types.Part.from_uri(
                file_uri=file.uri,
                mime_type=file.mime_type,
            )
        )

    # Add text instruction - Modified to include OCR verbatim request
    parts.append(
        types.Part.from_text(
            text=textwrap.dedent(
                f"""
                Parse this invoice and provide the output as a JSON object according to the schema.

                In addition to the structured JSON output, please also provide a field called "ocr_verbatim" which contains the full raw text extracted from the invoice using OCR.  Include all text content from all pages of the invoice in the "ocr_verbatim" field, even text that is not relevant to the structured JSON output.

                Extract all relevant details including invoice number, dates, vendor information, restaurant details, line items, amounts, payment information, and any other important data.
                """
            )
        )
    )

    contents = [
        types.Content(
            role="user",
            parts=parts,
        )
    ]

    # Define schema for invoice parsing - Added ocr_verbatim field
    invoice_schema = genai.types.Schema(
        type=genai.types.Type.OBJECT,
        properties={
            "invoice_number": genai.types.Schema(
                type=genai.types.Type.STRING,
                description="The unique identifier for the invoice"
            ),
            "invoice_date": genai.types.Schema(
                type=genai.types.Type.STRING,
                description="The date the invoice was issued"
            ),
            "vendor": genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "name": genai.types.Schema(type=genai.types.Type.STRING, description="Vendor company name"),
                    "address": genai.types.Schema(type=genai.types.Type.STRING, description="Vendor address"),
                    "tel": genai.types.Schema(type=genai.types.Type.STRING, description="Vendor contact phone number")
                }
            ),
            "ship_to": genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "name": genai.types.Schema(type=genai.types.Type.STRING, description="Restaurant name (e.g. DAN MODERN CHINESE #4)"),
                    # Future edit: locations
                    "location": genai.types.Schema(type=genai.types.Type.STRING, description="Extracted location name from the ship_to name (either PLAYA VISTA, SAWTELLE, SANTA MONICA, MANHATTAN BEACH, PASADENA, LONG BEACH, TOPANGA VILLAGE)"),
                    "address": genai.types.Schema(type=genai.types.Type.STRING, description="Restaurant address"),
                }
            ),
            "line_items": genai.types.Schema(
                type=genai.types.Type.ARRAY,
                items=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    properties={
                        "item_name": genai.types.Schema(type=genai.types.Type.STRING, description="Name of the item"),
                        "total_weight": genai.types.Schema(type=genai.types.Type.NUMBER, description="Total Weight"),
                        "unit_measure": genai.types.Schema(type=genai.types.Type.STRING, description="Unit of measurement (e.g., cs, bg, pk, etc.)"),
                        "quantity": genai.types.Schema(type=genai.types.Type.NUMBER, description="Quantity of the item"),
                        "unit_price": genai.types.Schema(type=genai.types.Type.NUMBER, description="Price per unit"),
                        "total_price": genai.types.Schema(type=genai.types.Type.NUMBER, description="Total price for the line item"),
                    }
                )
            ),
            "subtotal": genai.types.Schema(type=genai.types.Type.NUMBER, description="Sum of all line item totals before tax and discounts"),
            "tax": genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "tax_rate": genai.types.Schema(type=genai.types.Type.NUMBER, description="Tax rate percentage"),
                    "tax_amount": genai.types.Schema(type=genai.types.Type.NUMBER, description="Total tax amount"),
                    "tax_type": genai.types.Schema(type=genai.types.Type.STRING, description="Type of tax (e.g., VAT, Sales Tax)")
                }
            ),
            "total_amount": genai.types.Schema(type=genai.types.Type.NUMBER, description="Final total amount including tax and discounts")
        }
        #,required=["ocr_verbatim"]
    )


def find_invoice_groups(base_dir):
    """
    Find groups of invoice images by navigating folder structure.
    Assumes each subfolder contains images for a single invoice.

    Args:
        base_dir (str): Base directory containing invoice folders

    Returns:
        dict: Dictionary mapping invoice IDs to lists of image paths
    """
    invoice_groups = {}

    # Get all subdirectories
    for root, dirs, files in sorted(os.walk(base_dir)):
        if root == base_dir:
            continue

        # Get all image files in this directory
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.tiff']:
            image_files.extend(glob.glob(os.path.join(root, ext)))

        if image_files:
            # Sort the files to maintain page order
            image_files.sort()

            # Use the directory name as the invoice ID
            invoice_id = os.path.basename(root)
            invoice_groups[invoice_id] = image_files

    return invoice_groups


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Parse invoice images to JSON.")
    # parser.add_argument(
    #     "invoices_dir",
    #     nargs="?",  # Optional argument
    #     default="invoices",
    #     help="Base directory containing invoice folders (default: 'invoices' in current directory)",
    # )
    # parser.add_argument(
    #     "--output_dir",
    #     default="parsed_invoices",
    #     help="Directory to save parsed JSONs (default: 'parsed_invoices')",
    # )
    args = parser.parse_args()

    base_dir = "/Users/jiwonhur/dan_invoice/LT-Manhattan Beach" # Your base directory
    output_dir = "/Users/jiwonhur/dan_invoice/LT-Manhattan Beach/parsed_invoices" # Output directory

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Find groups of invoice images
    invoice_groups = find_invoice_groups(base_dir)

    if not invoice_groups:
        print(f"No invoice images found in {base_dir}")
        return

    print(f"Found {len(invoice_groups)} invoice groups")

    # Process each invoice group
    for invoice_id, image_paths in invoice_groups.items():
        print(f"Processing invoice {invoice_id} with {len(image_paths)} images")

        invoice_data = parse_invoice(image_paths)

        if invoice_data:
            filename = f"{invoice_id}.json"

            # Save the JSON file
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(invoice_data, f, ensure_ascii=False, indent=2, sort_keys=False)

            print(f"Saved parsed invoice to {output_path}")
        else:
            print(f"Failed to parse invoice {invoice_id}")


if __name__ == "__main__":
    main()