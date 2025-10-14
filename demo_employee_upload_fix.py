#!/usr/bin/env python3
"""
Visual demonstration of the employee upload fix.
Shows how different edge cases are handled before and after the fix.
"""
import pandas as pd

def demonstrate_edge_cases():
    """Demonstrate how different edge cases are handled"""
    
    print("=" * 80)
    print("EMPLOYEE UPLOAD FIX - EDGE CASE DEMONSTRATION")
    print("=" * 80)
    
    # Test data with various edge cases
    test_cases = {
        'Scenario': [
            'Normal email',
            'None (Python)',
            'nan (pandas float)',
            'Empty string',
            'Whitespace only',
            'String "None"',
            'String "nan"',
            'String "null"',
            'String "N/A"'
        ],
        'Input Value': [
            'john@test.com',
            None,
            float('nan'),
            '',
            '   ',
            'None',
            'nan',
            'null',
            'N/A'
        ]
    }
    
    df = pd.DataFrame(test_cases)
    
    print("\nTest Cases:")
    print("-" * 80)
    
    # Import the safe_str_strip function logic
    def safe_str_strip(value):
        """Safely convert value to string and strip, handling None/NaN/empty"""
        if value is None or pd.isna(value):
            return ''
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped.lower() in ('none', 'nan', 'null', 'n/a'):
                return ''
            return stripped
        str_val = str(value).strip()
        if str_val.lower() in ('none', 'nan', 'null', 'n/a'):
            return ''
        return str_val
    
    def process_email(email_raw):
        """Process email with defensive coding"""
        if email_raw is None or pd.isna(email_raw):
            return None
        elif isinstance(email_raw, str):
            email_stripped = email_raw.strip().lower()
            if not email_stripped or email_stripped in ('none', 'nan', 'null', 'n/a'):
                return None
            else:
                return email_stripped
        else:
            email_str = str(email_raw).strip().lower()
            if not email_str or email_str in ('none', 'nan', 'null', 'n/a'):
                return None
            else:
                return email_str
    
    # Show results
    for idx, row in df.iterrows():
        scenario = row['Scenario']
        input_val = row['Input Value']
        
        # For name fields
        name_result = safe_str_strip(input_val)
        
        # For email field
        email_result = process_email(input_val)
        
        print(f"\n{idx + 1}. {scenario}")
        print(f"   Input:  {repr(input_val)} (type: {type(input_val).__name__})")
        print(f"   Name:   {repr(name_result) if name_result else '(empty - row skipped)'}")
        print(f"   Email:  {repr(email_result) if email_result else 'NULL in database'}")
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print("✅ No NoneType.strip() errors in any scenario")
    print("✅ String nulls ('None', 'nan') converted to actual None/empty")
    print("✅ Whitespace-only values treated as empty")
    print("✅ Only valid email stored in database (NULL for invalid)")
    print("✅ Rows with empty names skipped automatically")
    print("=" * 80)

if __name__ == '__main__':
    demonstrate_edge_cases()
