"""
Simple test script to verify the API is working.
Run this after starting the backend server.

Usage:
    python test_api.py

Requires:
    requests library: pip install requests
"""

import requests
import json
from pathlib import Path


BASE_URL = "http://localhost:8000/api"


def test_health():
    """Test health endpoint."""
    print("\n" + "="*70)
    print("TEST: Health Check")
    print("="*70)

    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    print("✅ PASS")


def test_list_templates():
    """Test listing templates."""
    print("\n" + "="*70)
    print("TEST: List Templates")
    print("="*70)

    response = requests.get(f"{BASE_URL}/templates")
    print(f"Status: {response.status_code}")

    templates = response.json()
    print(f"Templates found: {len(templates)}")
    for t in templates[:3]:
        print(f"  - {t['name']}: {t['description']}")

    assert response.status_code == 200
    assert len(templates) > 0
    print("✅ PASS")


def test_get_template_schema():
    """Test getting template schema."""
    print("\n" + "="*70)
    print("TEST: Get Template Schema (Mutual-NDA)")
    print("="*70)

    response = requests.get(f"{BASE_URL}/templates/Mutual-NDA/schema")
    print(f"Status: {response.status_code}")

    schema = response.json()
    print(f"\nTemplate: {schema['name']}")
    print(f"Description: {schema['description']}")
    print(f"\nFields ({len(schema['fields'])} total):")

    for field in schema['fields']:
        required = "required" if field['required'] else "optional"
        field_type = field['type']
        print(f"  - {field['name']} ({field_type}, {required})")
        if field.get('description'):
            print(f"    {field['description']}")

    assert response.status_code == 200
    assert schema['name'] == 'Mutual-NDA'
    assert len(schema['fields']) > 0
    print("\n✅ PASS")


def test_generate_document():
    """Test document generation."""
    print("\n" + "="*70)
    print("TEST: Generate Document (Mutual-NDA)")
    print("="*70)

    payload = {
        "template": "Mutual-NDA",
        "fields": {
            "Purpose": "Evaluation of potential partnership and collaboration opportunities",
            "Effective Date": "2024-01-15",
            "MNDA Term": "2 years",
            "Term of Confidentiality": "3 years from the date of disclosure",
            "Governing Law": "California",
            "Jurisdiction": "Northern District of California",
            "Party A Name": "TechCorp Innovation Inc.",
            "Party A Address": "123 Innovation Drive, San Francisco, CA 94102, USA",
            "Party B Name": "AI Labs LLC",
            "Party B Address": "456 Research Boulevard, Palo Alto, CA 94301, USA"
        }
    }

    print("\nRequest body:")
    print(json.dumps(payload, indent=2)[:500] + "...")

    response = requests.post(f"{BASE_URL}/documents/generate", json=payload)
    print(f"\nStatus: {response.status_code}")

    if response.status_code == 201:
        result = response.json()
        print(f"Response:")
        print(f"  Document ID: {result['document_id']}")
        print(f"  Filename: {result['filename']}")
        print(f"  Download URL: {result['download_url']}")
        print(f"  Created At: {result['created_at']}")

        assert response.status_code == 201
        assert 'document_id' in result
        assert 'download_url' in result
        print("\n✅ PASS")

        return result['document_id']
    else:
        print(f"Error: {response.text}")
        print("❌ FAIL")
        return None


def test_download_document(document_id):
    """Test downloading a document."""
    print("\n" + "="*70)
    print("TEST: Download Document")
    print("="*70)

    if not document_id:
        print("Skipped (no document_id from previous test)")
        return

    response = requests.get(f"{BASE_URL}/documents/download/{document_id}")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {len(response.content)} bytes")

    assert response.status_code == 200
    assert response.headers.get('Content-Type') == 'application/pdf'
    assert len(response.content) > 0

    # Optionally save the file
    filename = f"test_output_{document_id}.pdf"
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f"File saved: {filename}")

    print("✅ PASS")


def test_get_api_info():
    """Test getting API info."""
    print("\n" + "="*70)
    print("TEST: Get API Info")
    print("="*70)

    response = requests.get(f"{BASE_URL}/info")
    print(f"Status: {response.status_code}")

    info = response.json()
    print(f"Name: {info['name']}")
    print(f"Version: {info['version']}")
    print(f"Template Count: {info['template_count']}")

    assert response.status_code == 200
    assert info['name'] == 'NDA Creator API'
    print("✅ PASS")


def test_error_cases():
    """Test error handling."""
    print("\n" + "="*70)
    print("TEST: Error Cases")
    print("="*70)

    # Test 1: Non-existent template
    print("\n1. Non-existent template:")
    response = requests.get(f"{BASE_URL}/templates/NonExistent/schema")
    print(f"   Status: {response.status_code}")
    assert response.status_code == 404
    print("   ✅ PASS")

    # Test 2: Missing required field
    print("\n2. Missing required fields:")
    payload = {
        "template": "Mutual-NDA",
        "fields": {
            "Purpose": "Test"
            # Missing other required fields
        }
    }
    response = requests.post(f"{BASE_URL}/documents/generate", json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        error = response.json()
        print(f"   Error: {error.get('detail', error)}")
    assert response.status_code == 400
    print("   ✅ PASS")

    # Test 3: Invalid template name in generate
    print("\n3. Invalid template in generation:")
    payload = {
        "template": "InvalidTemplate",
        "fields": {"Purpose": "Test"}
    }
    response = requests.post(f"{BASE_URL}/documents/generate", json=payload)
    print(f"   Status: {response.status_code}")
    assert response.status_code == 404
    print("   ✅ PASS")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("NDA Creator API - Test Suite")
    print("="*70)

    try:
        # Test basic endpoints
        test_health()
        test_list_templates()
        test_get_api_info()
        test_get_template_schema()

        # Test document generation and download
        document_id = test_generate_document()
        if document_id:
            test_download_document(document_id)

        # Test error cases
        test_error_cases()

        # Summary
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nNext steps:")
        print("1. Visit http://localhost:8000/docs for interactive API documentation")
        print("2. Check the generated_documents/ folder for PDF files")
        print("3. Try modifying the test data and re-running tests")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server!")
        print("Make sure the backend is running:")
        print("  python main.py")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
