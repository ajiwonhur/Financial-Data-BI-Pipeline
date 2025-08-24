# Invoice Processing and Reporting Pipeline

Python application that automatically parses invoice images using Google's Gemini AI to extract structured data and upload it to Google Sheets.

## 🚀 **What This Code Does**

This application processes invoice images and converts them into structured JSON data by:

1. **Image Processing**: Uploads invoice images to Google's Gemini AI service
2. **AI Analysis**: Uses Gemini 2.0 Flash model to extract invoice information
3. **Data Extraction**: Parses key invoice details including:
   - Invoice number and date
   - Vendor information (name, address, phone)
   - Restaurant/ship-to details with location extraction
   - Line items with quantities, weights, and pricing
4. **Output Generation**: Creates structured JSON files for each processed invoice
5. **Google Sheets Integration**: Automatically uploads parsed data to Google Sheets

## ✨ **Features**

- **Multi-format Support**: Handles PNG, JPG, JPEG, GIF, BMP, and TIFF images
- **Batch Processing**: Processes multiple invoice images automatically
- **Location Detection**: Automatically extracts restaurant locations
- **Complete Data Coverage**: Ensures all schema fields are present
- **Structured Output**: Generates consistent JSON format for easy data analysis
- **Google Sheets Integration**: Direct upload to spreadsheets for analysis

## 📋 **Prerequisites**

- Python 3.7+
- Google Gemini API key
- Google Service Account credentials
- Google Sheets spreadsheet
- Invoice images in organized folder structure

## 🛠️ **Installation**

1. **Clone this repository**
2. **Install required dependencies**:
```bash
pip install google-genai gspread python-dotenv
```

3. **Set up environment variables** by creating a `.env` file:
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

## 🔑 **Google Setup Requirements**

### 1. **Google Gemini API**
- Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- Create an API key
- Add to your `.env` file

### 2. **Google Service Account**
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project or select existing
- Enable Google Sheets API
- Create a service account
- Download the JSON credentials file
- Add the file path to your `.env` file

### 3. **Google Sheets**
- Create a new Google Sheet
- Share it with your service account email
- Copy the spreadsheet ID from the URL
- Add to your `.env` file

## 📁 **Folder Structure**

The application expects invoices to be organized as follows:
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

## 🚀 **Usage**

### **Basic Usage**
```bash
python invoice_processing_v2_original.py
```

### **Environment Variable Configuration**
The application automatically reads configuration from your `.env` file. Make sure all required variables are set before running.

## 📊 **Output**

### **JSON Files**
Processed invoices are saved as JSON files in the output directory, with each file containing:
- Structured invoice data
- All fields from the defined schema
- Missing fields set to null for consistency

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

## 🔧 **Configuration**

### **Environment Variables**
| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API key | None |
| `GOOGLE_SHEETS_ID` | ✅ | Google Sheets spreadsheet ID | None |
| `SERVICE_ACCOUNT_FILE` | ✅ | Path to service account credentials | None |
| `INVOICE_BASE_DIR` | ❌ | Base directory for invoice images | "invoices" |
| `INVOICE_OUTPUT_DIR` | ❌ | Output directory for parsed files | "parsed_invoices" |

## 📋 **Schema**

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

## 🚨 **Error Handling**

- **File upload failures**: Logged and processing continues
- **Missing images**: Logged and skipped
- **API errors**: Detailed error messages provided
- **Missing environment variables**: Clear error messages for missing configuration

## 🔒 **Security Notes**

- **API keys are loaded from environment variables** (not hardcoded)
- **No sensitive data is stored in the source code**
- **Service account credentials are loaded from external files**
- **Ensure `.env` files are not committed to version control**

## 📁 **File Structure**

```
project/
├── invoice_processing_v2_original.py  # Main processing script
├── README.md                          # This documentation
├── .env                               # Environment variables (create this)
├── .gitignore                         # Git ignore file
└── service_account_cred.json          # Google credentials (don't commit)
```

## 🚫 **What NOT to Commit**

- `.env` file (contains your API keys)
- `service_account_cred.json` (contains credentials)
- Invoice image files (can be large)
- Output JSON files (generated automatically)

## 📝 **Dependencies**

- `google-genai`: Google Gemini AI client library
- `gspread`: Google Sheets integration
- `python-dotenv`: Environment variable management
- `os`, `json`, `glob`, `textwrap`: Python standard library modules

**Note**: This application is designed for processing restaurant invoice data and includes specific business logic for DAN MODERN CHINESE locations. Modify the schema and processing logic as needed for your specific use case.
