[![Login Ubuntu](https://github.com/gridai-actions/gridai-login/actions/workflows/unittest-ubuntu.yml/badge.svg)](https://github.com/gridai-actions/gridai-login/actions/workflows/unittest-ubuntu.yml) 
[![Login Mac](https://github.com/gridai-actions/gridai-login/actions/workflows/unittest-mac.yml/badge.svg)](https://github.com/gridai-actions/gridai-login/actions/workflows/unittest-mac.yml) 
[![Login Win](https://github.com/gridai-actions/gridai-login/actions/workflows/unittest-win.yml/badge.svg)](https://github.com/gridai-actions/gridai-login/actions/workflows/unittest-win.yml)

 Install Python modules and login to Grid.ai.  

# Overview

This action performs the following:
- Install python 3.8
- Run `pip install lightning-grid`
- Run `grid login --username xxx -key xxx`

# Usage
Below is [unittest.yml](./.github/workflows/unittest.yml). In the production usage, replace `main` with the current stable build `v0`. 

```
jobs:
  unittests:
    strategy:
      matrix:
        os: [ubuntu-latest,macos-latest,windows-latest]         
        python-version: [3.8,3.9]   
        python-venv: ["","venv"]       
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v2     
      - uses: gridai-actions/gridai-login@main
        with:
          python-version: ${{ matrix.python-version }}
          gridai-username: ${{ secrets.GRIDAI_USERNAME }} 
          gridai-key: ${{ secrets.GRIDAI_KEY }}  
```

# Parameters

## Required
-  gridai-username:
    - required: true
    - default:
    - type: string
    - description: "Grid.ai username used in grid login command"
-  gridai-key:
    - required: true
    - default:
    - type: string
    - description: "Grid.ai key used in grid login command"

## Optional
-  grid-url:  
    -  required: false
    -  default: 
    -  type: string
    -  description: "URL to reach Grid.ai services"
-  python-version:  
    - required: false
    - default: 3.8    
    - type: string
    - description: "3.8 is the minimum Python version required for Grid.ai"
-  gridai-python-modules:  
    - required: false
    - default: "lightning-grid requests_toolbelt"
    - type: string
    - description: "Space separate list of Python modules to install"
-  add-module-version:  
    - required: false
    - default: "true"
    - type: string
    - description: "Suffix the latest Python module version. eg: lightning-grid to lightning-grid=0.4.1 (for example)"

# 

- to stop all Runs in ques / pending state
```
./gridai.py cli "grid status" --cli_chain True status_to_csv --array 1 | jq -r '.[][1]' | tail -n +2 | xargs -ot grid delete run 
```

- grid user
  
```
::set-output name=display_name::xxx
::set-output name=userid::xxx
::set-output name=username::xxx
::set-output name=email::xxx
::set-output name=teams::team name
::set-output name=role::role name
(gridai) robertlee@Roberts-MacBook-Pro gridai_action_login % grid login --username sangkyulee@gmail.com  --key dddcdbe7-d180-4638-8cca-19fafe4a33eb

Login successful. Welcome to Grid.
(gridai) robertlee@Roberts-MacBook-Pro gridai_action_login % gridai.py cli "grid user" status_to_kv --gha True                                     
::set-output name=display_name::xxx
::set-output name=userid::xxx
::set-output name=username::xxx
::set-output name=email::xxx
```  

- delete the old results

```
brew install gh
repo=gridai-run
repo=gridai-session

ghdelete() {
local repo=$1
gh api repos/gridai-actions/${repo}/actions/runs \
| jq -r '.workflow_runs[] | select(.head_branch != "master") | "\(.id)"' \
| xargs -n1 -I '{}' gh api repos/gridai-actions/${repo}/actions/runs/{} -X DELETE --silent
}

# https://stackoverflow.com/questions/57927115/anyone-know-a-way-to-delete-a-workflow-from-github-actions/65374631#65374631
# list workflows 
gh api repos/gridai-actions/${repo}/actions/workflows
# list runs from a workflow id=14772578
gh api repos/gridai-actions/${repo}/actions/workflows/14772578/runs
#

gh api repos/gridai-actions/${repo}/actions/runs/14772578 -X DELETE




- delete the workflow (which then needs to be restarted) 
```
ghdelete() {
local repo=$1
local org=${2:-gridai-actions}
# Get workflow IDs with status "disabled_manually"
workflow_ids=($(gh api repos/$org/$repo/actions/workflows | jq '.workflows[] | select(.["state"] | contains("disabled_manually")) | .id'))

for workflow_id in "${workflow_ids[@]}"
do
  echo "Listing runs for the workflow ID $workflow_id"
  run_ids=( $(gh api repos/$org/$repo/actions/workflows/$workflow_id/runs --paginate | jq '.workflow_runs[].id') )
  for run_id in "${run_ids[@]}"
  do
    echo "Deleting Run ID $run_id"
    gh api repos/$org/$repo/actions/runs/$run_id -X DELETE >/dev/null
  done
done
}
```

- delete just the runs

```
gh
gh repos/$org/$repo/actions/workflows  list # Pick-up the workflow ID for which you want to delete all runs
WORKFLOW_ID=<the workflow id> # Change this line!


gh api repos/$org/$repo/actions/workflows | jq '.workflows[] | .id'
gh api repos/$org/$repo/actions/workflows | jq '.workflows[] | [.id, .path] | @tsv'


```