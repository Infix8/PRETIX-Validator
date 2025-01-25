# Pretix Roll Number Validator

A Pretix plugin to validate and ensure unique roll numbers during ticket purchases, specifically designed for educational institutions.

## Features

- Validates roll number format (e.g., CSE001, ECE-002)
- Ensures unique roll numbers per event
- Supports predefined list of valid students
- Department code validation
- Case-insensitive matching
- Bulk import of student data via CSV
- Caching for better performance

## Installation

### Prerequisites

- Pretix 4.0.0 or newer
- Python 3.8 or newer
- Access to your Pretix installation

### Manual Installation

1. **Switch to Pretix User**
   ```bash
   sudo su pretix
   ```

2. **Activate Virtual Environment**
   ```bash
   source /var/pretix/venv/bin/activate
   ```

3. **Install the Plugin**
   ```bash
   # If installing from PyPI (recommended)
   pip3 install pretix-rollno-validator

   # If installing from Git
   pip3 install -U "git+https://github.com/yourusername/pretix-rollno-validator.git@main#egg=pretix-rollno-validator"
   ```

4. **Apply Database Migrations**
   ```bash
   python -m pretix migrate
   ```

5. **Rebuild Static Files**
   ```bash
   python -m pretix rebuild
   ```

6. **Restart Pretix Services**
   ```bash
   sudo systemctl restart pretix-web pretix-worker
   ```

### Development Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/pretix-rollno-validator.git
   cd pretix-rollno-validator
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run Tests**
   ```bash
   pytest
   ```

## Configuration

1. **Enable the Plugin**
   - Go to Settings → Plugins
   - Enable "Roll Number Validator"

2. **Configure Roll Number Settings**
   - Go to Settings → Roll Number Settings
   - Select which question should be validated for uniqueness
   - Optionally configure valid department codes

3. **Import Student Data**
   - Go to Settings → Roll Number Settings → Import Students
   - Upload CSV file with student data
   - Required columns: roll_number, name, department
   - Optional columns: email, batch, is_active

### CSV Format Example
```csv
roll_number,name,department,email,batch,is_active
CSE001,John Doe,Computer Science,john@example.com,2024,true
ECE001,Jane Smith,Electronics,jane@example.com,2024,true
```

## Usage

1. **Create Roll Number Question**
   - Create a new question in your event
   - Set type as "Text"
   - Mark as "Required"
   - Use identifier "roll_number"

2. **Configure Validation**
   - Go to plugin settings
   - Select the roll number question
   - Configure department codes if needed

3. **Student Purchase Flow**
   - Students enter their roll number during ticket purchase
   - Plugin validates:
     - Roll number format
     - Department code
     - Uniqueness
     - Against predefined list (if configured)

## Error Messages

Students will see clear error messages for:
- Invalid roll number format
- Invalid department code
- Duplicate roll numbers
- Roll numbers not in predefined list

## Troubleshooting

1. **Plugin Not Appearing**
   - Check if plugin is installed: `pip list | grep pretix-rollno`
   - Verify Pretix version compatibility
   - Check error logs: `/var/log/pretix/`

2. **Validation Not Working**
   - Verify question is selected in plugin settings
   - Check if roll number format matches requirements
   - Look for error messages in Pretix logs

3. **Import Issues**
   - Verify CSV format and encoding (must be UTF-8)
   - Check required columns are present
   - Look for specific error messages during import

## Support

For bug reports and feature requests, please use the [GitHub issue tracker](https://github.com/yourusername/pretix-rollno-validator/issues).

## License

Released under the Apache License 2.0

## Contributing

1. Fork the repository
2. Create your feature branch
3. Install development dependencies
4. Run tests before submitting PR
5. Submit Pull Request

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_validation.py

# Run with coverage
pytest --cov=pretix_rollno_validator

# Run with verbose output
pytest -v
```

### Code Style
```bash
# Check style
flake8 pretix_rollno_validator

# Format code
black pretix_rollno_validator
``` 