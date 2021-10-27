[![Grid.ai Login Test](https://github.com/gridai-actions/gridai-login/actions/workflows/unittest.yml/badge.svg)](https://github.com/gridai-actions/gridai-login/actions/workflows/unittest.yml)

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
        os: [ubuntu-latest,macos-latest,windows-latest]         # os: [macos-latest, ubuntu-latest, windows-latest]
        python-version: [3.8,3.9]       # [3.8, 3.9]
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
