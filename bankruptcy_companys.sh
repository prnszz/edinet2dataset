#!/bin/bash

echo "Starting parallel downloads..."

echo "Downloading 船井電機株式会社 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "船井電機株式会社" --doc_type annual &

echo "Downloading 日本電解株式会社 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "日本電解株式会社" --doc_type annual &

echo "Downloading 株式会社ガイアックス data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "株式会社ガイアックス" --doc_type annual &

echo "Downloading ユニゾホールディングス株式会社 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "ユニゾホールディングス株式会社" --doc_type annual &

echo "Downloading 株式会社アイ・テック data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "株式会社アイ・テック" --doc_type annual &

echo "Downloading 株式会社レナウン data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "株式会社レナウン" --doc_type annual &

echo "Downloading 株式会社ベクトル data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "株式会社ベクトル" --doc_type annual &

echo "Downloading 株式会社　オーテック data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "株式会社　オーテック" --doc_type annual &

echo "Downloading ＳＢＩ　ＦｉｎＴｅｃｈ　Ｓｏｌｕｔｉｏｎｓ株式会社 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "ＳＢＩ　ＦｉｎＴｅｃｈ　Ｓｏｌｕｔｉｏｎｓ株式会社" --doc_type annual &

echo "Waiting for all downloads to complete..."
wait

echo "All downloads completed!"

echo "Starting to parse all downloaded TSV files..."
mkdir -p parsed_outputs

find data/ -name "*.tsv" -type f | while read file; do
    echo "Parsing: $file"
    
    filename=$(basename "$file" .tsv)
    
    uv run python src/edinet2dataset/parser.py \
        --file_path "$file" \
        --category_list BS PL CF SUMMARY TEXT META \
        --output_path "parsed_outputs/${filename}_parsed.json"
    
    echo "Parsed: $file -> parsed_outputs/${filename}_parsed.json"
done

echo "All parsing completed!"