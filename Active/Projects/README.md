# Invoice Parser

A Python application that automatically parses invoice images using Google's Gemini AI to extract structured data and OCR text.

## What This Code Does

This application processes invoice images and converts them into structured JSON data by:

1. **Image Processing**: Uploads invoice images to Google's Gemini AI service
2. **AI Analysis**: Uses Gemini 2.0 Flash model to extract invoice information
3. **Data Extraction**: Parses key invoice details including:
   - Invoice number and date
   - Vendor information (name, address, phone)
   - Restaurant/ship-to details with location extraction
   - Line items with quantities, weights, and pricing
   - Tax information and totals
   - Full OCR verbatim text from all pages
4. **Output Generation**: Creates structured JSON files for each processed invoice

## Features

- **Multi-page Support**: Handles invoices with multiple images/pages
- **Location Detection**: Automatically extracts restaurant locations (Playa Vista, Sawtelle, Santa Monica, Manhattan Beach, Pasadena, Long Beach, Topanga Village)
- **Complete Data Coverage**: Ensures all schema fields are present, even if missing from source
- **Batch Processing**: Processes multiple invoice folders automatically
- **Structured Output**: Generates consistent JSON format for easy data analysis

## Prerequisites

- Python 3.7+
- Google Gemini API key
- Invoice images in organized folder structure

## Installation

1. Clone this repository
2. Install required dependencies:
```bash
pip install google-genai
```

3. Set your Gemini API key as an environment variable:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

## Usage

### Basic Usage

```bash
python "import os.py"
```

### Folder Structure

The application expects invoices to be organized as follows:
```
base_directory/
├── invoice_folder_1/
│   ├── page1.jpg
│   ├── page2.jpg
│   └── page3.png
├── invoice_folder_2/
│   ├── page1.jpg
│   └── page2.jpg
└── ...
```

### Output

Processed invoices are saved as JSON files in the `parsed_invoices` directory, with each file containing:
- Structured invoice data
- Complete OCR text extraction
- All fields from the defined schema (missing fields set to null)

## Configuration

The application is currently configured to process invoices from:
- **Input Directory**: `/Users/jiwonhur/dan_invoice/LT-Manhattan Beach`
- **Output Directory**: `/Users/jiwonhur/dan_invoice/LT-Manhattan Beach/parsed_invoices`

To modify these paths, edit the `main()` function in the script.

## Schema

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
  ],
  "subtotal": "number",
  "tax": {
    "tax_rate": "number",
    "tax_amount": "number",
    "tax_type": "string"
  },
  "total_amount": "number"
}
```

## Error Handling

- File upload failures stop processing for that invoice
- Missing or corrupted images are logged
- Processing continues with remaining invoices

## Security Notes

- API keys are loaded from environment variables (not hardcoded)
- No sensitive data is stored in the source code
- Ensure `.env` files are not committed to version control

## Dependencies

- `google-genai`: Google Gemini AI client library
- `os`, `json`, `glob`, `argparse`, `textwrap`: Python standard library modules

## License

[Add your license information here]

## Contributing

[Add contribution guidelines if applicable] 