import requests
import re
import xml.etree.ElementTree as ET
from typing import List, Dict
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def parse_xml_response(xml_text: str) -> List[Dict]:
    """解析 PubMed 返回的 XML 数据，提取标题、摘要、PMID 等信息"""
    articles = []
    root = ET.fromstring(xml_text)

    # 遍历每篇文献
    for article in root.findall(".//PubmedArticle"):
        # 提取 PMID
        pmid = article.find(".//PMID").text

        # 提取标题
        title = article.find(".//ArticleTitle").text

        # 提取摘要（可能分段）
        abstract_elements = article.findall(".//AbstractText")
        abstract = " ".join([elem.text for elem in abstract_elements if elem.text])

        articles.append({
            "pmid": pmid,
            "title": title,
            "abstract": abstract
        })

    return articles


def parse_query_with_ollama(user_query: str) -> Dict:
    """通过 Ollama API 解析用户查询"""
    api_url = "http://localhost:11434/api/generate"
    prompt = (
        "解析用户查询为 JSON，包含 keywords、year、type 字段。\n"
        "示例输入：'找近3年肺癌免疫治疗文献' → "
        '{"keywords": ["肺癌", "免疫治疗"], "year": 3, "type": ""}\n'
        f"实际输入：{user_query}"
    )

    try:
        response = requests.post(
            api_url,
            json={
                "model": "deepseek-r1:7b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            }
        )
        response.raise_for_status()
        parsed_str = response.json()["response"]
        # 使用正则表达式提取 JSON 内容
        match = re.search(r'```json\s*([\s\S]*?)\s*```', parsed_str)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON 解析错误: {e}，输入字符串: {json_str}")
        else:
            print("未找到有效的 JSON 代码块")
        return {"keywords": [], "year": 0, "type": ""}
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 错误: {e}，状态码: {e.response.status_code}，响应内容: {e.response.text}")
        return {"keywords": [], "year": 0, "type": ""}
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return {"keywords": [], "year": 0, "type": ""}
    except Exception as e:
        print(f"其他错误: {e}")
        return {"keywords": [], "year": 0, "type": ""}



def search_pubMed(parsed_query):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": " AND ".join(parsed_query["keywords"]) + " AND " + f"({parsed_query['year']}[PDAT])",
        "retmode": "json",
        "retmax": 50  # 返回最大文献数
    }

    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)

    try:
        response = session.get(base_url, params=params)
        response.raise_for_status()
        pmids = response.json()["esearchresult"]["idlist"]
        return pmids
    except requests.exceptions.HTTPError as e:
        print(f"搜索 PubMed 时发生 HTTP 错误: {e}")
        return []
    except Exception as e:
        print(f"搜索 PubMed 时发生其他错误: {e}")
        return []



def get_article_details(pmids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        # 解析XML（可使用xml.etree.ElementTree）
        articles = parse_xml_response(response.text)
        return articles  # 返回结构化数据列表
    except requests.exceptions.HTTPError as e:
        print(f"获取文献详情时发生 HTTP 错误: {e}")
        return []
    except Exception as e:
        print(f"获取文献详情时发生其他错误: {e}")
        return []


# 用户输入
user_query = input("给出你的需求")

# 解析查询
parsed_query = parse_query_with_ollama(user_query)

# 搜索PubMed
pmids = search_pubMed(parsed_query)

# 获取文献详情
articles = get_article_details(pmids)

# 输出结果（示例）
for article in articles:
    print(f"标题: {article['title']}")
    print(f"摘要: {article['abstract']}")
    print(f"链接: https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}\n")