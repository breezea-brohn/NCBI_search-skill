#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import argparse
import time
from Bio import Entrez
import xml.etree.ElementTree as ET

# ====================== 基础配置 ======================
Entrez.email = "breezeabrohn@gmail.com"  
Entrez.api_key = "98f9e9363aacc0d06234693f14bf93d91508" 
Entrez.sleep_between_requests = 0.5 # 遵守 NCBI 频率限制

def get_gene_info(gene_name: str, species: str = "human"):
    """
    【升级二】：查询 NCBI Gene 数据库，获取基因官方总结和别名。
    这能帮助 Agent 在搜索文献前先理解基因的生物学背景。
    """
    try:
        query = f"{gene_name}[Gene Name] AND {species}[Organism]"
        handle = Entrez.esearch(db="gene", term=query, retmax=1)
        record = Entrez.read(handle)
        handle.close()
        gene_ids = record.get("IdList", [])
        
        if not gene_ids:
            return {"success": True, "found": False, "message": f"未找到基因: {gene_name}"}

        # 获取详细 XML
        handle = Entrez.efetch(db="gene", id=gene_ids[0], rettype="xml", retmode="text")
        xml_content = handle.read()
        handle.close()
        root = ET.fromstring(xml_content)
        
        # 提取官方总结、别名和染色体位置
        summary = root.findtext(".//Entrezgene_summary", "暂无官方总结。")
        aliases = root.findtext(".//Gene-ref_syn", "无别名")
        location = root.findtext(".//Gene-ref_maploc", "未知")
        description = root.findtext(".//Gene-ref_desc", "N/A")
        
        return {
            "success": True,
            "found": True,
            "data": {
                "gene_id": gene_ids[0],
                "symbol": gene_name,
                "description": description,
                "location": location,
                "aliases": aliases,
                "summary": summary
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Gene API 错误: {str(e)}"}

def search_pubmed(query: str, max_results: int = 5):
    """
    【升级一】：在检索文献的同时，提取 MeSH (医学主题词)。
    MeSH 词能让 Agent 无需阅读长文本就能精准把握研究领域。
    """
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        id_list = record.get("IdList", [])
        
        if not id_list:
            return {"success": True, "resultCount": 0, "results": []}

        fetch_handle = Entrez.efetch(db="pubmed", id=",".join(id_list), rettype="xml", retmode="text")
        xml_data = fetch_handle.read()
        fetch_handle.close()

        root = ET.fromstring(xml_data)
        papers = []
        
        for article in root.findall('.//PubmedArticle'):
            pmid = article.findtext('.//PMID', 'N/A')
            year = article.findtext('.//PubDate/Year', 'N/A')
            title = article.findtext('.//ArticleTitle', 'N/A')
            
            # 提取摘要
            abstract_texts = article.findall('.//AbstractText')
            abstract = " ".join([text.text for text in abstract_texts if text.text])
            if not abstract:
                abstract = "无摘要。"
                
            # --- 【升级一核心代码】：提取 MeSH 主题词 ---
            mesh_terms = []
            for mesh in article.findall('.//MeshHeading/DescriptorName'):
                if mesh.text:
                    mesh_terms.append(mesh.text)
            
            papers.append({
                "pmid": pmid,
                "year": year,
                "title": title,
                "mesh_terms": mesh_terms, # 结构化标签
                "abstract": abstract
            })
            
        return {
            "success": True, 
            "query": query,
            "resultCount": len(papers), 
            "results": papers
        }

    except Exception as e:
         return {"success": False, "error": f"PubMed API 错误: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description="NCBI 综合检索工具 - 课设增强版")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 子命令 1: search (文献检索)
    search_parser = subparsers.add_parser("search", help="搜索 PubMed 文献")
    search_parser.add_argument("query", type=str, help="检索关键词")
    search_parser.add_argument("--max", type=int, default=5, help="最大返回数量")

    # 子命令 2: gene (基因百科)
    gene_parser = subparsers.add_parser("gene", help="查询基因官方信息")
    gene_parser.add_argument("symbol", type=str, help="基因符号 (如 CSF2)")
    gene_parser.add_argument("--species", type=str, default="human", help="物种 (默认 human)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    result = {}
    if args.command == "search":
        result = search_pubmed(args.query, args.max)
    elif args.command == "gene":
        result = get_gene_info(args.symbol, args.species)
    else:
        result = {"success": False, "error": "未知命令"}

    # 以标准 JSON 格式输出，确保 OpenClaw Agent 能解析
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
