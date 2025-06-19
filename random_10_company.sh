#!/bin/bash

echo "Starting parallel downloads..."

echo "Downloading ナトコ株式会社 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "ナトコ株式会社" --doc_type annual &

echo "Downloading ユニチカ株式会社 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "ユニチカ株式会社" --doc_type annual &

echo "Downloading 株式会社エプコ data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "株式会社エプコ" --doc_type annual &

echo "Downloading 和弘食品株式会社data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "和弘食品株式会社" --doc_type annual &

echo "Downloading 株式会社ボルテージ data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "株式会社ボルテージ" --doc_type annual &

echo "Downloading 丸大食品株式会社 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "丸大食品株式会社" --doc_type annual &

echo "Downloading 東亜ディーケーケー株式会社 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "東亜ディーケーケー株式会社" --doc_type annual &

echo "Downloading 沖縄セルラー電話株式会社 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "沖縄セルラー電話株式会社" --doc_type annual &

echo "Downloading 株式会社石井表記 data..." &
uv run python src/edinet2dataset/downloader.py --start_date 2020-01-01 --end_date 2024-12-31 --company_name "株式会社石井表記" --doc_type annual &

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