import os
import requests
from requests.auth import HTTPBasicAuth
import json

headers = {
    "Accept": "application/json", 
    "Content-Type": "application/json"
}

def get_publisher_config():
    pub_config = None
    try:
        pub_json = os.environ.get("PUBLISHER_DATA", "{}")
        pub_data = json.loads(pub_json)
        pub_config = {
            "domain": pub_data["domain"],
            "project": pub_data["project"],
            "auth": HTTPBasicAuth(pub_data["email"], pub_data["token"])
        }
    except Exception as e:
        print(f"Failed to parse PUBLISHER_DATA JSON: {str(e)}")
    return pub_config

def get_subscriber_configs():
    configs = []
    try:
        raw_json = os.environ.get("SUBSCRIBER_DATA", "[]")
        subscriber_list = json.loads(raw_json)
        for sub in subscriber_list:
            configs.append({
                "domain": sub["domain"],
                "project": sub["project"],
                "auth": HTTPBasicAuth(sub["email"], sub["token"])
            })
    except Exception as e:
        print(f"Failed to parse SUBSCRIBER_DATA JSON: {str(e)}")
    return configs

def get_updated_issues(config, minutes_ago):
    url = f"{config['domain']}/rest/api/3/search/jql"
    jql = f'project = "{config["project"]}" AND updated >= -{minutes_ago}m'
    query = {
        'jql': jql, 
        'fields': 'status'
    }
    auth = config['auth']
    response = requests.request("GET", url, headers=headers, params=query, auth=auth)
    return response.json().get('issues', []) if response.status_code == 200 else []

def get_target_issues(config, sync_key):
    url = f"{config['domain']}/rest/api/3/search/jql"
    jql = f'project = "{config["project"]}" AND description ~ "\\"{sync_key}\\""'
    query = {
        'jql': jql,
        'fields': 'status'
    }
    auth = config['auth']
    response = requests.request("GET", url, headers=headers, params=query, auth=auth)
    return response.json().get('issues', []) if response.status_code == 200 else []

def get_transitions(config, issue_key):
    url = f"{config['domain']}/rest/api/3/issue/{issue_key}/transitions"
    auth = config['auth']
    response = requests.request("GET", url, headers=headers, auth=auth)
    return response.json().get('transitions', []) if response.status_code == 200 else []

def set_status(config, issue, transition_id, target_status):
    url = f"{config['domain']}/rest/api/3/issue/{issue['key']}/transitions"
    payload = json.dumps({
        "transition": {
            "id": transition_id
        }
    })
    auth = config['auth']
    response = requests.request("POST", url, data=payload, headers=headers, auth=auth)
    if response.status_code == 204:
        print(f"Successfully updated {issue['key']} to '{target_status}'")
    else:
        print(f"Failed to update {issue['key']}'s status")

def sync_issues(pub_issue, sub_config, sub_issues):  
    pub_status = pub_issue['fields']['status']['name']
    for sub_issue in sub_issues:
        sub_status = sub_issue['fields']['status']['name']  
        if pub_status != sub_status:
            print(f"Updating: {pub_issue['key']} ({pub_status}) -> Sub {sub_issue['key']} ({sub_status})")
            
            transitions = get_transitions(sub_config, sub_issue['key'])
            transition_id = None
            
            for transition in transitions:
                if transition['to']['name'].lower() == pub_status.lower():
                    transition_id = transition['id']
                    break
            
            if not transition_id:
                print(f"Status '{pub_status}' does not exist on {sub_issue['key']}. Skipping.")
                continue
            
            set_status(sub_config, sub_issue, transition_id, pub_status)

def sync_boards():
    pub_config = get_publisher_config()
    if not pub_config:
        print("No publisher configured.")
        return
    sub_configs = get_subscriber_configs()
    if not sub_configs:
        print("No subscribers configured.")
        return
    pub_issues = get_updated_issues(pub_config, minutes_ago=70)
    for pub_issue in pub_issues:
        sync_key = f"[Sync-ID: {pub_issue['key']}]"
        for sub_config in sub_configs:  
            sub_issues = get_target_issues(sub_config, sync_key)
            sync_issues(pub_issue, sub_config, sub_issues)

def lambda_handler(event, context):
    try:
        sync_boards()
        return {'statusCode': 200, 'body': json.dumps('Sync loop complete.')}
    except Exception as e:
        print(f"Failed: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps(str(e))}

def load_env():
    with open('.env', 'r') as env_file:
        for line in env_file:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k.strip()] = v.strip()

if __name__ == "__main__":
    if os.path.exists('.env'):
        load_env()
    lambda_handler({}, None)