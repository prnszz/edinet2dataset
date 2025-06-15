import json
import glob
import os
import pandas as pd
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
    
    # Output as CSV format (flattened data)
    csv_output = f"merged_edinet_data_{timestamp}.csv"
    try:
        # Create flattened data structure
        flattened_data = []
        
        for company_data in merged_data:
            flat_record = {}
            
            # Basic information
            if 'META' in company_data:
                for key, value in company_data['META'].items():
                    flat_record[f"META_{key}"] = value
            
            # Financial summary
            if 'SUMMARY' in company_data:
                for key, value in company_data['SUMMARY'].items():
                    if isinstance(value, dict):
                        for year, amount in value.items():
                            flat_record[f"SUMMARY_{key}_{year}"] = amount
                    else:
                        flat_record[f"SUMMARY_{key}"] = value
            
            # Balance sheet key items
            if 'BS' in company_data:
                key_bs_items = ['総資産', '純資産', '現金及び預金', '負債']
                for item in key_bs_items:
                    if item in company_data['BS']:
                        bs_data = company_data['BS'][item]
                        if isinstance(bs_data, dict):
                            for year, amount in bs_data.items():
                                flat_record[f"BS_{item}_{year}"] = amount
                        else:
                            flat_record[f"BS_{item}"] = bs_data
            
            # Profit and loss key items
            if 'PL' in company_data:
                key_pl_items = ['売上高', '営業利益', '経常利益', '当期利益']
                for item in key_pl_items:
                    if item in company_data['PL']:
                        pl_data = company_data['PL'][item]
                        if isinstance(pl_data, dict):
                            for year, amount in pl_data.items():
                                flat_record[f"PL_{item}_{year}"] = amount
                        else:
                            flat_record[f"PL_{item}"] = pl_data
            
            # Cash flow key items
            if 'CF' in company_data:
                key_cf_items = ['営業キャッシュフロー', '投資キャッシュフロー', '財務キャッシュフロー']
                for item in key_cf_items:
                    if item in company_data['CF']:
                        cf_data = company_data['CF'][item]
                        if isinstance(cf_data, dict):
                            for year, amount in cf_data.items():
                                flat_record[f"CF_{item}_{year}"] = amount
                        else:
                            flat_record[f"CF_{item}"] = cf_data
            
            # Add source file info
            flat_record['source_file'] = company_data.get('source_file', '')
            
            flattened_data.append(flat_record)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(flattened_data)
        df.to_csv(csv_output, index=False, encoding='utf-8-sig')
        print(f"✅ CSV file saved: {csv_output}")
        print(f"📊 CSV contains {len(df)} rows, {len(df.columns)} columns")
        
    except Exception as e:
        print(f"❌ Failed to save CSV: {e}")
    
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
