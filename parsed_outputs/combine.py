import json
import glob
import os
from datetime import datetime

def merge_json_files():
    """Merge all JSON files"""
    
    # Get all JSON files in the current directory
    json_files = glob.glob("*.json")
    
    if not json_files:
        print("❌ No JSON files found")
        return
    
    print(f"📁 Found {len(json_files)} JSON files")
    
    merged_data = []
    failed_files = []
    
    for file_path in json_files:
        try:
            print(f"📖 Reading: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['META']['倒産'] = "true"  # Mark as bankruptcy for all 
            # Add file name as identifier
            data['source_file'] = file_path
            merged_data.append(data)
            
        except Exception as e:
            print(f"❌ Failed to read file {file_path}: {e}")
            failed_files.append(file_path)
    
    if not merged_data:
        print("❌ No files were successfully read")
        return
    
    # Generate output file name (with timestamp)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Output as JSON format
    json_output = f"merged_edinet_data_{timestamp}.json"
    try:
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON file saved: {json_output}")
    except Exception as e:
        print(f"❌ Failed to save JSON: {e}")
    
    # Output statistics
    print(f"\n📈 Merge summary:")
    print(f"  - Successfully processed: {len(merged_data)} files")
    print(f"  - Failed files: {len(failed_files)}")
    if failed_files:
        print(f"  - Failed list: {', '.join(failed_files)}")
    
    # Show basic company information
    print(f"\n🏢 Included companies:")
    for i, data in enumerate(merged_data[:10], 1):  # Show only first 10
        company_name = "Unknown"
        edinet_code = "Unknown"
        
        if 'META' in data:
            company_name = data['META'].get('会社名', 'Unknown')
            edinet_code = data['META'].get('EDINETコード', 'Unknown')
        
        print(f"  {i}. {company_name} ({edinet_code})")
    
    if len(merged_data) > 10:
        print(f"  ... and {len(merged_data) - 10} more companies")

if __name__ == "__main__":
    print("🚀 Starting EDINET financial data merge...")
    print(f"📂 Current directory: {os.getcwd()}")
    
    merge_json_files()
    
    print("\n✨ Merge completed!")