# Invoice Processing and Reporting Pipeline

Python application that automatically parses invoice images using Google's Gemini AI to extract structured data and upload it to Google Sheets.

**Note**: This application was designed for processing invoice data for Dan Modern business. Modify the schema and processing logic as needed for your specific use case.

## Overview 

This application processes invoice images and converts them into structured JSON data by:

1. **Invoice Image Processing**: Uploads invoice images to Google's Gemini AI service
2. **Data Extraction**: Parses key invoice details including:
   - Invoice number and date
   - Vendor information (name, address, phone)
   - Restaurant/ship-to details with location extraction
   - Line items with quantities, weights, and pricing
3. **Data Transformation in JSON foramt**: Creates structured JSON files for each processed invoice
4. **Data Load to Google Sheets**: Uploads parsed data to Google Sheets using G sheet service account

## **Prerequisites**

- Google Gemini API key
- Google Service Account credentials
- Google Sheets spreadsheet
- Invoice images in organized folder structure

1. **Install required dependencies**:
```bash
pip install google-genai gspread python-dotenv
```

2. **Set up environment variables** by creating a `.env` file:
```bash
# Required: Your Google Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# Required: Your Google Sheets spreadsheet ID
GOOGLE_SHEETS_ID=your_spreadsheet_id_here

# Required: Path to your Google service account credentials JSON file
SERVICE_ACCOUNT_FILE=/path/to/your/service_account_cred.json

# Optional: Base directory containing invoice images (defaults to "invoices")
INVOICE_BASE_DIR=/path/to/your/invoice/folder

# Optional: Output directory for parsed invoices (defaults to "parsed_invoices")
INVOICE_OUTPUT_DIR=/path/to/your/output/folder
```

3. **Prepare invoice folder structure**: The application expects invoices to be organized as follows:
```
base_directory/
├── invoice_folder_1/
│   ├── invoice1.jpg
│   ├── invoice2.png
│   └── invoice3.tiff
├── invoice_folder_2/
│   ├── invoice4.jpg
│   └── invoice5.png
└── ...
```


## **Output**

### **JSON Files**
Processed invoices are saved as JSON files in the output directory, with each file containing:
- Structured invoice data
- All fields from the defined schema
- Missing fields set to null 

### Schema

The output JSON follows this structure:
```json
{
  "invoice_number": "string",
  "invoice_date": "string",
  "vendor": {
    "name": "string",
    "address": "string",
    "tel": "string"
  },
  "ship_to": {
    "name": "string",
    "location": "string",
    "address": "string"
  },
  "line_items": [
    {
      "item_name": "string",
      "total_weight": "number",
      "unit_measure": "string",
      "quantity": "number",
      "unit_price": "number",
      "total_price": "number"
    }
  ]
}
```

### **Google Sheets**
Data is automatically uploaded to your specified Google Sheet with columns:
- Invoice Number
- Invoice Date
- Vendor
- Ship To Name
- DMC Location
- Item Name
- Quantity
- Total Weight
- Unit Measure
- Unit Price
- Total Price

## Dependencies
- `google-genai`: Google Gemini AI client library
- `gspread`: Google Sheets integration
- `python-dotenv`: Environment variable management
- `os`, `json`, `glob`, `textwrap`: Python standard library modules
