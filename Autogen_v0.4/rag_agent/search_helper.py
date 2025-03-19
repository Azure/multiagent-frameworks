from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
    SearchIndex,
    AzureOpenAIVectorizer,
    AzureOpenAIParameters
)
import json
from dotenv import load_dotenv
from pathlib import Path 
import os
import requests
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.search.documents.models import VectorizableTextQuery

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
import os
import openai_helper
from datetime import datetime
import uuid
from typing import List
from dotenv import load_dotenv


load_dotenv()


# The following variables from your .env file are used in this notebook
azure_search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
credential = AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY", "")) if len(os.getenv("AZURE_SEARCH_API_KEY", "")) > 0 else DefaultAzureCredential()
index_name = "aml_index_2" #os.getenv("AZURE_SEARCH_INDEX", "vectest")
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT","")
azure_openai_key = os.getenv("AZURE_OPENAI_KEY", "") if len(os.getenv("AZURE_OPENAI_KEY", "")) > 0 else None
azure_openai_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
azure_openai_embedding__large_deployment = os.getenv("AZURE_OPENAI_3_LARGE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
azure_openai_embedding__small_deployment = os.getenv("AZURE_OPENAI_3_LARGE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
azure_openai_embedding_large_dimensions = int(os.getenv("AZURE_OPENAI_EMBEDDING_LARGE_DIMENSIONS", 3072))
azure_openai_embedding_small_dimensions = int(os.getenv("AZURE_OPENAI_EMBEDDING_SMALLDIMENSIONS", 1536))
embedding_model_name = os.getenv("AZURE_OPENAI_3_LARGE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
azure_document_intelligence_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "https://document-intelligence.api.cognitive.microsoft.com/")
azure_document_intelligence_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")

# print all the above
#print(azure_search_endpoint)
#print(credential)
#print(index_name)
#print(azure_openai_endpoint)
#print(azure_openai_embedding__large_deployment)
#print(azure_openai_embedding_large_dimensions)
#print(azure_openai_embedding_small_dimensions)
#print(embedding_model_name)
#print(azure_openai_api_version)
#print(azure_document_intelligence_endpoint)

doc_intelli_credential = AzureKeyCredential(azure_document_intelligence_key)
document_intelligence_client = DocumentIntelligenceClient(azure_document_intelligence_endpoint, doc_intelli_credential)

index_client = SearchIndexClient(
    endpoint=azure_search_endpoint, credential=credential)


def create_index(index_name: str, analyzer_name: str = "en.microsoft", language_suffix: str = "en"):
        index_schema = {
        "name": index_name,
        "fields": [
            {
                "name": "id",
                "type": "Edm.String",
                "key": True,
                "sortable": True,
                "filterable": True,
                "facetable": True
            },
            {
                "name": "docName",
                "type": "Edm.String",
                "searchable": True
            },
            {
                "name": "pageNumber",
                "type": "Edm.String",
                "searchable": True
            },
            {
                "name": f"title_{language_suffix}",
                "type": "Edm.String",
                "analyzer": analyzer_name,
                "searchable": True
            },
            {
                "name": f"content_{language_suffix}",
                "type": "Edm.String",
                "analyzer": analyzer_name,
                "searchable": True
            },
            {
                "name": f"category_{language_suffix}",
                "type": "Collection(Edm.String)",
                "analyzer": analyzer_name,
                "filterable": True,
                "searchable": True
            },
            {
                "name": f"tags_{language_suffix}",
                "type": "Collection(Edm.String)",
                "analyzer": analyzer_name,
                "filterable": True,
                "searchable": True
            },
            {
                "name": "lastUpdated",
                "type": "Edm.DateTimeOffset"
            
            },
            {
                "name": "titleVector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "dimensions": 1536,
                "vectorSearchProfile": "amlHnswProfile",
            },
            {
                "name": "contentVector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "dimensions": 3072,
                "vectorSearchProfile": "amlHnswProfile",
            },
            {
                "name": "categoryVector",
                "type": "Collection(Edm.Single)",
            "searchable": True,
                "dimensions": 1536,
                "vectorSearchProfile": "amlHnswProfile",
            },
            {
                "name": "tagsVector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "dimensions": 1536,
                "vectorSearchProfile": "amlHnswProfile",
            }
        ],
        "scoringProfiles": [
            {
            "name": "tagsBoost",
            "text": {
                "weights": {
                f"tags_{language_suffix}": 5
                }
            },
                "functions": []
            },
            {
            "name": "newAndLatest",
            "functionAggregation": "sum",
            "functions": [
                {
                    "fieldName": "lastUpdated",
                    "interpolation": "quadratic",
                    "type": "freshness",
                    "boost": 10,
                    "freshness": {
                            "boostingDuration": "P365D"
                        }
            
                }
            ]
            }
        ],
        "suggesters": [
            {
                "name": "sg",
                "searchMode": "analyzingInfixMatching",
                "sourceFields": [f"title_{language_suffix}"]
            }
        ],
        "vectorSearch": {
                "algorithms": [
                    {
                        "name": "amlHnsw",
                        "kind": "hnsw",
                        "hnswParameters": {
                        "m": 4,
                        "metric": "cosine"
                        }
                    }
                
                ],
                "profiles": [
                    {
                        "name": "amlHnswProfile",
                        "algorithm": "amlHnsw",
                        "vectorizer": "amlVectorizer"
                    }
                
                ], 
                "vectorizers": [
                    {
                        "name":"amlVectorizer",
                        "kind":"azureOpenAI",
                        "azureOpenAIParameters": {
                            "resourceUri": azure_openai_endpoint,
                            "deploymentId": azure_openai_embedding__large_deployment,
                            "modelName": embedding_model_name,
                            "apiKey": azure_openai_key
                        }
                    }
                ]
                
    },
        "semantic": {
            "configurations": [
                {
                    "name": "aml-semantic-config",
                    "prioritizedFields": {
                        "titleField": {
                            "fieldName": f"title_{language_suffix}"
                        },
                        "prioritizedKeywordsFields": [
                            {
                                "fieldName": f"category_{language_suffix}"
                            },
                            {
                                "fieldName": f"tags_{language_suffix}"
                            }
                        ],
                        "prioritizedContentFields": [
                            {
                                "fieldName": f"content_{language_suffix}"
                            }
                        ]
                    }
                }
            ]
        }
    }



        headers = {'Content-Type': 'application/json',
                'api-key': os.getenv("AZURE_SEARCH_ADMIN_KEY", "") }
        # Create Index
        url = azure_search_endpoint + "/indexes/" + index_name + "?api-version=2024-07-01"


        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            response  = requests.put(url, headers=headers, json=index_schema)
            index = response.json()
            print(index)
        else:
            print("Index already exists")

def get_document_layout(pdf_folder, doc_name):
    with open(os.path.join(pdf_folder ,doc_name), "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout", analyze_request=f, content_type="application/octet-stream"
        )
    return poller.result()

def extract_pdf_data(pdf_folder, extract_folder):
     doc_names = [os.listdir(pdf_folder)[i] for i in range(0, len(os.listdir(pdf_folder)))]
     for doc_idx, doc_name in enumerate(doc_names):
        # Get the document layout
        document_data = []
        print(f"Analyzing document: {doc_name}")
        result = get_document_layout(pdf_folder, doc_name)
        print(f"Layout analysis completed for document: {doc_name}")
        print(f"Processing document: {doc_name}...")
        for page in result.pages:
            if page.lines:
                page_text = ""
                for line_idx, line in enumerate(page.lines):
                    #print(f"Line {line_idx}: {line.content}")
                    page_text +=  line.content + " "

                doc_data = {
                    "doc_name": doc_name,
                    "page_number": page.page_number,
                    "line_number": line_idx,
                    "content": page_text
                }
                document_data.append(doc_data)

        output_file_path = os.path.join(extract_folder, doc_names[doc_idx] + "-document_data.json")
        with open(output_file_path, "w") as f:
            json.dump(document_data, f)


def enrich_pdf_data(extracted_data_folder, output_file_name):
    aml_index_data = []
    system_message = """
    You are an AI assitant who can extract title, topics and cateogries from a document.
    You will be given a document and you need to extract the title, topics and categories from the document in json format.
    Retain the language in the document while extracting the title, topics and categories.
    Title: Extract the title of the document that captures the information in the document in the original document language.
    Topics: Extract the topics from the document that best describe the content in the original document language.
    Categories: Extract the categories from the document that best describe the content in the original document language.
    Do not write ```json and ``` in your response.

    json format:
    {
        "title": "Document Title"
        "topics": ["topic1 in the do", "topic2"],
        "categories": ["category1", "category2"]
    }
    """
    for ex_data in os.listdir(extracted_data_folder):
        #print(f"Processing extracted data: {ex_data}")
        with open(os.path.join(extracted_data_folder, ex_data), "r") as f:
            aml_docs_json = json.loads( f.read())
            print(f"Processing document: {f.name}")
            for doc in aml_docs_json:
                #print(f"Processing document: {doc['doc_name']}")
                user_query = f"""Extract the Title, topics and categories from the document.
                            
                            Document:

                            {doc["content"]}
                            """
                try:
                    llm_reponse =openai_helper.getOpenAIResp(user_query)
                    llm_json = json.loads(llm_reponse)
                    aml_index_item = {
                        "id": str(uuid.uuid4()),
                        "doc_name": doc["doc_name"],
                        "page_number": doc["page_number"],
                        "title": llm_json["title"],
                        "content": doc["content"],
                        "category": json.dumps(llm_json["categories"]),
                        "tags": json.dumps(llm_json["topics"]),
                        "lastupdated": str(datetime.now())
                    }

                    aml_index_data.append(aml_index_item)
                except Exception as e:
                    with open("error.log", "a") as f:
                        f.write(f"Error processing document: {doc['doc_name']}, {doc['page_number']} - {e}\n")
                    print(f"Error processing document: {doc['doc_name']}, {doc['page_number']} - {e}")

    with open(output_file_name, "w") as f:
        json.dump(aml_index_data, f) 
        


def enrich_with_embeddings(output_file_name):
    with open(output_file_name, "r") as f:
        aml_index_data = json.loads(f.read())

    titles = []
    content = []
    categories = []
    tags = []
    for doc in aml_index_data:
        titles.append(doc["title"])
        content.append(doc["content"])
        categories.append(doc["category"])
        tags.append(doc["tags"])


    batch_size = 500

    for i in range(0, len(titles), batch_size):
        print(f"Processing batch: {i}")
        title_embeddings = openai_helper.generate_embeddings(titles[i:i+batch_size], dimensions=azure_openai_embedding_small_dimensions,
                                                model=azure_openai_embedding__small_deployment)
        content_embeddings = openai_helper.generate_embeddings(content[i:i+batch_size], dimensions=azure_openai_embedding_large_dimensions,
                                                model=azure_openai_embedding__large_deployment)
        category_embeddings = openai_helper.generate_embeddings(categories[i:i+batch_size],dimensions=azure_openai_embedding_small_dimensions,
                                                model=azure_openai_embedding__small_deployment)
        tags_embeddings = openai_helper.generate_embeddings(tags[i:i+batch_size],dimensions=azure_openai_embedding_small_dimensions, model=azure_openai_embedding__small_deployment)


        for j, (title_emb, content_emb, category_emb, tag_emb) in enumerate(zip(title_embeddings,
                        content_embeddings,
                        category_embeddings,
                        tags_embeddings)):
            aml_index_data[i+j]["titleVector"] = title_emb.embedding
            aml_index_data[i+j]["contentVector"] = content_emb.embedding
            aml_index_data[i+j]["categoryVector"] = category_emb.embedding
            aml_index_data[i+j]["tagsVector"] = tag_emb.embedding


        print(f"Embeddings generated for batch: {i}")

    vector_file_name = f"{output_file_name}_with_vectors.json"

    with open(vector_file_name, "w") as f:
        json.dump(aml_index_data, f)




def upload_to_search(index_name, data_file, language_suffix: str = "en"):
    
    vector_file_name = f"{data_file}_with_vectors.json"

    with open(vector_file_name, "r") as f:
        aml_index_data_with_vectors = json.loads(f.read())

    search_client = SearchClient(endpoint=azure_search_endpoint, index_name=index_name, credential=credential)

    for doc in aml_index_data_with_vectors:
        
        last_updated = datetime.fromisoformat(doc["lastupdated"]).isoformat() + "Z"
        search_doc = {
            "id": doc["id"],
            "docName": doc["doc_name"],
            "pageNumber": str(doc["page_number"]),
            f"title_{language_suffix}": doc["title"],
            f"content_{language_suffix}": doc["content"],
            f"category_{language_suffix}": json.loads(doc["category"]),
            f"tags_{language_suffix}": json.loads(doc["tags"]),
            "lastUpdated": last_updated,
            "titleVector": doc["titleVector"],
            "contentVector": doc["contentVector"],
            "categoryVector": doc["categoryVector"],
            "tagsVector": doc["tagsVector"]
        }

        result = search_client.upload_documents(documents=[search_doc])

    print(f"{len(aml_index_data_with_vectors)} Documents uploaded to Azure Search")


def get_index_fields(index_name):
    index_client = SearchIndexClient(
        endpoint=azure_search_endpoint, credential=credential)
    idx = index_client.get_index(index_name)
    select_fields = []
    vector_fields =  []
    for field in idx.fields:
        #print(field.name)
        if(field.type == SearchFieldDataType.String):
            select_fields.append(field.name)
        if(str.find(field.name, "Vector") > 0):
            vector_fields.append(field.name)
    return select_fields, vector_fields

async def retrieve_search_results(index_name: str, search_query: str, top_k: int = 3) -> str:
    select_fields, vector_fields = get_index_fields(index_name)  
    #select_fields = ["title", "content", "category", "tags"]
    search_client = SearchClient(endpoint=azure_search_endpoint, index_name=index_name, credential=credential)
    #vector_query = VectorizableTextQuery(text=search_query, k_nearest_neighbors=3, fields=search_fields, exhaustive=True)
  
    vector_queries  = [VectorizableTextQuery(text=search_query, k_nearest_neighbors=top_k, fields=field) for field in vector_fields]
    results = search_client.search(  
        search_text=search_query,  
        vector_queries= vector_queries,
        select=select_fields,
        top=top_k
    )  

    json_results = []
    for result in results:
        field_results = []
        for field in select_fields:
            result_dict = {
                field: result[field]
            }
            field_results.append(result_dict)
        json_results.append(field_results)
    print(json_results)
    return f"<Context>{ json.dumps(json_results)} </Context>"



