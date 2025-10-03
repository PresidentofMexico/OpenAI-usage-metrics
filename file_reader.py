"""
Robust file reading utilities for CSV and Excel files with encoding detection
and error handling specifically designed for Streamlit file uploads.
"""

import pandas as pd
import io
import os
import chardet
from typing import Tuple, Optional
import streamlit as st


def detect_encoding(file_content: bytes) -> str:
    """
    Detect the encoding of a file using chardet.
    
    Args:
        file_content: Raw bytes content of the file
        
    Returns:
        Detected encoding string (e.g., 'utf-8', 'iso-8859-1')
    """
    result = chardet.detect(file_content)
    encoding = result.get('encoding', 'utf-8')
    confidence = result.get('confidence', 0)
    
    # If confidence is low, default to utf-8
    if confidence < 0.7:
        encoding = 'utf-8'
    
    return encoding


def read_csv_robust(uploaded_file, nrows: Optional[int] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Robustly read a CSV file with automatic encoding detection and error handling.
    
    This function handles common issues with CSV uploads in Streamlit:
    - Multiple encoding attempts (UTF-8, UTF-16, ISO-8859-1, CP1252)
    - File pointer reset after reading
    - Various CSV delimiters and quoting styles
    - Malformed CSV structure
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        nrows: Optional number of rows to read (for preview)
        
    Returns:
        Tuple of (DataFrame or None, error_message or None)
    """
    if uploaded_file is None:
        return None, "No file uploaded"
    
    # Reset file pointer to beginning
    try:
        uploaded_file.seek(0)
    except:
        pass
    
    # Read file content as bytes
    try:
        file_content = uploaded_file.getvalue()
    except Exception as e:
        return None, f"Cannot read file content: {str(e)}"
    
    # Validate file size (max 200MB)
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > 200:
        return None, f"File too large: {file_size_mb:.2f} MB (max 200 MB)"
    
    # Check if file is empty
    if len(file_content) == 0:
        return None, "File is empty"
    
    # Try to detect encoding
    detected_encoding = detect_encoding(file_content)
    
    # List of encodings to try in order
    encodings = [detected_encoding, 'utf-8', 'utf-16', 'iso-8859-1', 'cp1252', 'latin1']
    # Remove duplicates while preserving order
    encodings = list(dict.fromkeys(encodings))
    
    # List of common CSV delimiters to try
    delimiters = [',', ';', '\t', '|']
    
    last_error = None
    
    # Try each encoding
    for encoding in encodings:
        try:
            # Try to decode the file content
            text_content = file_content.decode(encoding)
            
            # Try different delimiters
            for delimiter in delimiters:
                try:
                    # Create StringIO from decoded content
                    string_buffer = io.StringIO(text_content)
                    
                    # Try to read CSV with current encoding and delimiter
                    df = pd.read_csv(
                        string_buffer,
                        encoding=encoding,
                        delimiter=delimiter,
                        nrows=nrows,
                        on_bad_lines='skip',  # Skip bad lines instead of failing
                        encoding_errors='replace'  # Replace encoding errors with ?
                    )
                    
                    # Validate that we got a non-empty dataframe with columns
                    if df is not None and not df.empty and len(df.columns) > 1:
                        # Reset file pointer for next read
                        try:
                            uploaded_file.seek(0)
                        except:
                            pass
                        return df, None
                    
                except Exception as e:
                    last_error = str(e)
                    continue
            
        except UnicodeDecodeError as e:
            last_error = f"Encoding error with {encoding}: {str(e)}"
            continue
        except Exception as e:
            last_error = f"Error with {encoding}: {str(e)}"
            continue
    
    # If all attempts failed, return error
    error_msg = f"Cannot parse CSV file. Last error: {last_error}"
    return None, error_msg


def read_excel_robust(uploaded_file, nrows: Optional[int] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Robustly read an Excel file with error handling.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        nrows: Optional number of rows to read (for preview)
        
    Returns:
        Tuple of (DataFrame or None, error_message or None)
    """
    if uploaded_file is None:
        return None, "No file uploaded"
    
    # Reset file pointer to beginning
    try:
        uploaded_file.seek(0)
    except:
        pass
    
    try:
        # Read file content
        file_content = uploaded_file.getvalue()
        
        # Validate file size (max 200MB)
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > 200:
            return None, f"File too large: {file_size_mb:.2f} MB (max 200 MB)"
        
        # Check if file is empty
        if len(file_content) == 0:
            return None, "File is empty"
        
        # Create BytesIO buffer
        bytes_buffer = io.BytesIO(file_content)
        
        # Try to read Excel file
        if nrows is not None:
            df = pd.read_excel(bytes_buffer, nrows=nrows)
        else:
            df = pd.read_excel(bytes_buffer)
        
        # Reset file pointer for next read
        try:
            uploaded_file.seek(0)
        except:
            pass
        
        return df, None
        
    except Exception as e:
        error_msg = f"Cannot parse Excel file: {str(e)}"
        return None, error_msg


def read_file_robust(uploaded_file, nrows: Optional[int] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Automatically detect file type and read robustly.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        nrows: Optional number of rows to read (for preview)
        
    Returns:
        Tuple of (DataFrame or None, error_message or None)
    """
    if uploaded_file is None:
        return None, "No file uploaded"
    
    filename = uploaded_file.name.lower()
    
    if filename.endswith('.csv'):
        return read_csv_robust(uploaded_file, nrows)
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        return read_excel_robust(uploaded_file, nrows)
    else:
        return None, f"Unsupported file format: {filename}"


def read_file_from_path(file_path: str, nrows: Optional[int] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Read a CSV or Excel file directly from a filesystem path.
    
    This function is similar to read_file_robust but works with file paths
    instead of Streamlit UploadedFile objects.
    
    Args:
        file_path: Path to the file on the filesystem
        nrows: Optional number of rows to read (for preview)
        
    Returns:
        Tuple of (DataFrame or None, error_message or None)
    """
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"
    
    filename = file_path.lower()
    
    try:
        if filename.endswith('.csv'):
            # Read CSV with encoding detection
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Validate file size (max 200MB)
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > 200:
                return None, f"File too large: {file_size_mb:.2f} MB (max 200 MB)"
            
            # Check if file is empty
            if len(file_content) == 0:
                return None, "File is empty"
            
            # Detect encoding
            detected_encoding = detect_encoding(file_content)
            
            # List of encodings to try
            encodings = [detected_encoding, 'utf-8', 'utf-16', 'iso-8859-1', 'cp1252', 'latin1']
            encodings = list(dict.fromkeys(encodings))
            
            # List of delimiters to try
            delimiters = [',', ';', '\t', '|']
            
            last_error = None
            
            # Try each encoding and delimiter combination
            for encoding in encodings:
                try:
                    text_content = file_content.decode(encoding)
                    
                    for delimiter in delimiters:
                        try:
                            string_buffer = io.StringIO(text_content)
                            df = pd.read_csv(
                                string_buffer,
                                encoding=encoding,
                                delimiter=delimiter,
                                nrows=nrows,
                                on_bad_lines='skip',
                                encoding_errors='replace'
                            )
                            
                            if df is not None and not df.empty and len(df.columns) > 1:
                                return df, None
                        
                        except Exception as e:
                            last_error = str(e)
                            continue
                
                except UnicodeDecodeError as e:
                    last_error = f"Encoding error with {encoding}: {str(e)}"
                    continue
                except Exception as e:
                    last_error = f"Error with {encoding}: {str(e)}"
                    continue
            
            return None, f"Cannot parse CSV file. Last error: {last_error}"
        
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            # Read Excel file
            if nrows is not None:
                df = pd.read_excel(file_path, nrows=nrows)
            else:
                df = pd.read_excel(file_path)
            
            return df, None
        
        else:
            return None, f"Unsupported file format: {filename}"
    
    except Exception as e:
        return None, f"Error reading file: {str(e)}"


def display_file_error(error_msg: str):
    """
    Display a user-friendly error message with troubleshooting tips.
    
    Args:
        error_msg: The error message to display
    """
    st.error(f"❌ **Error reading file:** {error_msg}")
    
    with st.expander("🔧 Troubleshooting Tips"):
        st.markdown("""
        **Common issues and solutions:**
        
        1. **Encoding Issues:**
           - Save your CSV file with UTF-8 encoding
           - In Excel: File → Save As → CSV UTF-8 (Comma delimited)
        
        2. **File Corruption:**
           - Open the file in a text editor to verify it's readable
           - Try re-exporting from the original source
        
        3. **Format Issues:**
           - Ensure your file has proper CSV structure with headers
           - Check that there are no special characters in column names
           - Verify the file uses comma (,) as delimiter
        
        4. **Excel Files:**
           - Ensure the file is in .xlsx format (not .xls)
           - Try saving as CSV instead
        
        5. **File Size:**
           - Maximum file size is 200 MB
           - Consider splitting large files into smaller chunks
        
        **Still having issues?**
        - Try opening the file in Excel/Sheets and re-saving it
        - Contact support with the error message above
        """)
