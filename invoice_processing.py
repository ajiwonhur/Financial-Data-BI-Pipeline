import os
import json
import glob
import textwrap
import gspread

from google import genai
from google.genai import types
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# GEMINI_API_KEY: Google Gemini API key
# GOOGLE_SHEETS_ID: Google Sheets spreadsheet ID
# SERVICE_ACCOUNT_FILE: Path to Google service account credentials JSON file
# INVOICE_BASE_DIR: Base directory containing raw invoice image files 
# INVOICE_OUTPUT_DIR: Output directory for parsed invoices

def ensure_all_fields_present(data, schema):
    """Ensures all schema fields are present in the data."""
    if not isinstance(data, dict):
        data = {}
    output_data = {}
    if schema.type == genai.types.Type.OBJECT and schema.properties:
        for prop_name, prop_schema in schema.properties.items():
            if prop_name in data:
                prop_value = data[prop_name]
                if prop_schema.type in [genai.types.Type.OBJECT, genai.types.Type.ARRAY]:
                    if isinstance(prop_value, dict):
                        output_data[prop_name] = ensure_all_fields_present(prop_value, prop_schema)
                    elif isinstance(prop_value, list) and prop_schema.items:
                        output_data[prop_name] = [ensure_all_fields_present(item, prop_schema.items) if isinstance(item, dict) else item for item in prop_value]
                    else:
                        output_data[prop_name] = ensure_all_fields_present({}, prop_schema) if prop_schema.type == genai.types.Type.OBJECT else [] if prop_schema.type == genai.types.Type.ARRAY else None
                else:
                    output_data[prop_name] = prop_value
            else:
                if prop_schema.type == genai.types.Type.OBJECT:
                    output_data[prop_name] = ensure_all_fields_present({}, prop_schema)
                elif prop_schema.type == genai.types.Type.ARRAY:
                    output_data[prop_name] = []
                else:
                    output_data[prop_name] = None
        return output_data
    elif schema.type == genai.types.Type.ARRAY and schema.items:
        if isinstance(data, list):
            return [ensure_all_fields_present(item, schema.items) if isinstance(item, dict) else item for item in data]
        else:
            return []
    return data


def parse_invoice(image_paths):
    """Parse all images of an invoice into a structured JSON."""
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

    if not image_paths:
        print("No image files provided to parse_invoice function!")
        return None

    print(f"parse_invoice received image_paths: {image_paths}")

    # Upload all files
    files = []
    for img_path in image_paths:
        try:
            uploaded_file = client.files.upload(file=img_path)
            files.append(uploaded_file)
            print(f"Uploaded file {img_path} to {uploaded_file.uri}")
        except Exception as e:
            print(f"Error uploading file {img_path}: {e}")
            continue

    if not files:
        print("No files were successfully uploaded for OCR.")
        return None

    model = "gemini-2.0-flash"
    parts = []
    for file in files:
        parts.append(
            types.Part.from_uri(
                file_uri=file.uri,
                mime_type=file.mime_type,
            )
        )

    parts.append(
        types.Part.from_text(
            text=textwrap.dedent(
                f"""
                Parse this invoice and provide the output as a JSON object according to the schema.
                Extract all relevant details including line items.
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
                    "name": genai.types.Schema(type=genai.types.Type.STRING, description="Vendor company name (either S.J. Distributors or L&T or A Farm)"),
                    "address": genai.types.Schema(type=genai.types.Type.STRING, description="Vendor address"),
                    "tel": genai.types.Schema(type=genai.types.Type.STRING, description="Vendor contact phone number")
                }
            ),
            "ship_to": genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "name": genai.types.Schema(type=genai.types.Type.STRING, description="Restaurant name (e.g. DAN MODERN CHINESE #4)"),
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
            )
        }
    )

    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_mime_type="application/json",
        response_schema=invoice_schema
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        invoice_data = json.loads(response.text)
        invoice_data = ensure_all_fields_present(invoice_data, invoice_schema)
        return invoice_data

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Problematic JSON Response Text: {response.text if 'response' in locals() and hasattr(response, 'text') else 'No response text available'}")
        return None
    except Exception as e:
        print(f"Error parsing invoice images: {str(e)}")
        return None


def find_invoice_image_files(base_dir):
    """Finds all invoice image files in the base directory and subdirectories."""
    image_files = []
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            # Check for images
            if any(glob.fnmatch.fnmatch(file.lower(), ext) for ext in ['*.png', '*.jpg', '*.jp2', '*.jpeg', '*.gif', '*.bmp', '*.tiff']):
                image_files.append(os.path.join(root, file))
    
    image_files.sort()
    return image_files


def json_to_tabular_data(invoice_data):
    """Transforms invoice JSON data to tabular format."""
    rows = []
    if invoice_data and invoice_data.get("line_items") and isinstance(invoice_data["line_items"], list):
        invoice_number = invoice_data.get("invoice_number", "")
        invoice_date = invoice_data.get("invoice_date", "")
        vendor_name = invoice_data.get("vendor", {}).get("name", "")
        shipto_name = invoice_data.get("ship_to", {}).get("name", "")
        dmc_location = invoice_data.get("ship_to", {}).get("location", "")

        for item in invoice_data["line_items"]:
                row_data = [
                    invoice_number,
                    invoice_date,
                    vendor_name,
                    shipto_name,
                    dmc_location,
                    item.get("item_name", ""),
                    item.get("quantity", ""),
                    item.get("total_weight", ""),
                    item.get("unit_measure", ""),
                    item.get("unit_price", ""),
                    item.get("total_price", "")
                ]
                rows.append(row_data)
    return rows


def load_to_google_sheets_gspread(tabular_data, spreadsheet_id, sheet_name, service_account_file):
    """Loads tabular data to Google Sheets using gspread."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    sheet = spreadsheet.worksheet(sheet_name)
    sheet.append_rows(tabular_data)


def main():
    base_dir = os.environ.get("INVOICE_BASE_DIR", "invoices")  
    output_dir = os.environ.get("INVOICE_OUTPUT_DIR", "parsed_invoices")  

    os.makedirs(output_dir, exist_ok=True)

    image_files = find_invoice_image_files(base_dir)
    if not image_files:
        print(f"No invoice files found in {base_dir}")
        return

    print("---- All invoice files found ----")
    print(f"Images: {image_files}")


    # Process invoice image files
    for image_file in image_files:
        print(f"\n--- Processing image: {image_file} ---")
        invoice_id = os.path.splitext(os.path.basename(image_file))[0]
        
        invoice_data = parse_invoice([image_file])
        if invoice_data:
            relative_path = os.path.relpath(image_file, base_dir)
            output_sub_dir = os.path.dirname(relative_path)
            output_file_dir = os.path.join(output_dir, output_sub_dir)
            os.makedirs(output_file_dir, exist_ok=True)
            
            output_filename = f"{invoice_id}.json"
            output_path = os.path.join(output_file_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(invoice_data, f, ensure_ascii=False, indent=2, sort_keys=False)
            print(f"Saved parsed invoice to {output_path}")
            
            tabular_data = json_to_tabular_data(invoice_data)
            if tabular_data:
                spreadsheet_id = os.environ.get("GOOGLE_SHEETS_ID")
                sheet_name = "Invoice data"
                service_account_file = os.environ.get("SERVICE_ACCOUNT_FILE")
                if spreadsheet_id and service_account_file:
                    load_to_google_sheets_gspread(tabular_data, spreadsheet_id, sheet_name, service_account_file)
                    print(f"Data for invoice {invoice_id} loaded to Google Sheet")
                else:
                    print(f"Missing environment variables for Google Sheets integration")
            else:
                print(f"No tabular data generated for invoice {invoice_id}")
        else:
            print(f"Failed to parse image {image_file}")

    print("\nProcessing completed for all files.")


if __name__ == "__main__":
    main()
