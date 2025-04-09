import dataiku

client = dataiku.api_client()
project = client.get_default_project()

def do(payload, config, plugin_config, inputs):
    
    analysis_details = project.list_analyses()
    
    choices = [
            {
                "value": item['analysisId'],
                "label": item['analysisName']
            }
            for item in analysis_details
        ]
    choices.append({"value": "new",
                "label": "+ Create New Analysis"})
    return {"choices": choices}