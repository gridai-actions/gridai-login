 Orchestrate Python installation, logging in to Grid.ai, and running lightning example via GitLab.  

# Overview
The gitlab-ci.yml performs the following:
- Install python 3.8
- Install git
- Installs grid cli
- Logs into Grid account utilizing variables saved in Gitlab

# Purpose
The purpose of this readme is to give an example of how to mirror a github repo and utilize gitlab-ci to instantiate experiments on Grid. It requires the following variables to be defined in your mirrored Gitlab settings:
1. GRID_USER
2. GRID_APIKEY

# Set Up Instructions
Follow the instructions here to connect Github repositories to Gitlab https://docs.gitlab.com/ee/ci/ci_cd_for_external_repos/github_integration.html.
Additionally, please read the following documentation if you are unfamiliar with Gitlab variables https://docs.gitlab.com/ee/ci/variables/.
