#!/usr/bin/env python3
"""
PDF to Layout-Preserving Text Converter
Batch processes PDF files using pdfplumber to extract text with physical layout preserved.
"""

import os
import sys
from pathlib import Path
import pdfplumber


def ensure_output_directory(output_dir):
    """Create output directory if it doesn't exist."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)


def extract_text_with_layout(pdf_path):
    """Extract text from PDF while preserving layout using pdfplumber."""
    extracted_text = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text with layout=True to preserve columns and positioning
                text = page.extract_text(layout=True)

                if text:
                    extracted_text.append(f"--- Page {page_num} ---")
                    extracted_text.append(text)
                    extracted_text.append("")  # Add blank line between pages
                else:
                    extracted_text.append(f"--- Page {page_num} ---")
                    extracted_text.append("(No text found on this page)")
                    extracted_text.append("")

        return "\n".join(extracted_text)

    except Exception as e:
        raise Exception(f"Error processing PDF {pdf_path}: {str(e)}")


def process_pdf_folder(input_folder="./samplepdf", output_folder="./debug_txt", progress_callback=None):
    """
    Process all PDF files in the input folder and its subdirectories, then save extracted text to output folder.

    Args:
        input_folder (str): Path to folder containing PDF files
        output_folder (str): Path to folder where text files will be saved
        progress_callback (callable, optional): Function to call with (current, total)
    """
    # Ensure input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return False

    # Ensure output directory exists
    ensure_output_directory(output_folder)

    # Get all PDF files in the input folder and subdirectories
    pdf_files = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))

    if not pdf_files:
        print(f"No PDF files found in '{input_folder}' or its subdirectories.")
        return False

    total_files = len(pdf_files)
    print(f"Found {total_files} PDF files to process...")

    success_count = 0
    error_count = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        # Update progress
        if progress_callback:
            try:
                progress_callback(i, total_files)
            except Exception:
                pass

        try:
            # Generate unique filename for output
            # Use relative path from input_folder to create unique names
            relative_path = os.path.relpath(pdf_path, input_folder)
            # Replace path separators with underscores to create flat filename
            unique_name = relative_path.replace(os.sep, '_').replace('/', '_')
            txt_filename = os.path.splitext(unique_name)[0] + '.txt'
            txt_path = os.path.join(output_folder, txt_filename)

            print(f"Processing ({i}/{total_files}): {relative_path}")

            # Extract text with layout preservation
            extracted_text = extract_text_with_layout(pdf_path)

            # Save extracted text to file
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(extracted_text)

            print(f"[OK] Success: {relative_path} processed and saved to {txt_filename}")
            success_count += 1

        except Exception as e:
            print(f"[ERROR] Error processing {os.path.relpath(pdf_path, input_folder)}: {str(e)}")
            error_count += 1

    # Print summary
    print(f"\nProcessing complete!")
    print(f"Successfully processed: {success_count} files")
    print(f"Errors encountered: {error_count} files")
    print(f"Output saved to: {os.path.abspath(output_folder)}")

    return success_count > 0


def main():
    """Main function to run the PDF conversion script."""
    print("PDF to Layout-Preserving Text Converter")
    print("=" * 50)

    # Check if pdfplumber is available
    try:
        import pdfplumber
    except ImportError:
        print("Error: pdfplumber library is not installed.")
        print("Please install it using: pip install pdfplumber")
        sys.exit(1)

    # Process PDFs with default folders
    success = process_pdf_folder()

    if success:
        print("\nAll PDFs processed successfully!")
    else:
        print("\nPDF processing encountered issues. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()