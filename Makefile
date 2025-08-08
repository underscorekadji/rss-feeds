SHELL := /bin/bash

.SILENT:

.PHONY: help
.DEFAULT_GOAL := help
help:  ## Prints all the targets in all the Makefiles
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: list
list:  ## List all make targets
	@${MAKE} -pRrn : -f $(MAKEFILE_LIST) 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | sort

##########################
### Env Common Targets ###
##########################

.PHONY: check-env
check-env: ## Checks if the virtual environment is activated
ifndef VIRTUAL_ENV
	$(error 'Virtualenv is not activated, please activate the Python virtual environment by running "$$(make env_source)".')
endif

.PHONY: env_create
env_create:  ## Create the virtual environment
	uv venv

.PHONY: env_source
env_source:  ## Source the env; must be execute like so: $(make env_source)
	@echo 'source .venv/bin/activate'

.PHONY: clean
clean:  ## Clean generated files and virtual environment
	rm -rf venv
	rm -rf .venv
	rm -rf feeds/*.xml

##########################
### Uvx Common Targets ###
##########################

.PHONY: uvx_install
uvx_install: ## Install dependencies using uv
	uv venv
	uv pip install -r requirements.txt

#############################
### Python Common Targets ###
#############################

.PHONY: py_format
py_format: check-env  ## Format the python code
	black .
	isort .

####################
### RSS Targets  ###
####################

.PHONY: generate_all_feeds
generate_all_feeds: check-env  ## Generate all RSS feeds
	python feed_generators/run_all_feeds.py

.PHONY: generate_anthropic_news_feed
generate_anthropic_news_feed: check-env  ## Generate RSS feed for anthropic/news
	python feed_generators/anthropic_news_blog.py

.PHONY: generate_anthropic_engineering_feed
generate_anthropic_engineering_feed: check-env  ## Generate RSS feed for anthropic/engineering
	python feed_generators/anthropic_eng_blog.py

.PHONY: generate_anthropic_research_feed
generate_anthropic_research_feed: check-env  ## Generate RSS feed for anthropic/research
	python feed_generators/anthropic_research_blog.py

.PHONY: generate_anthropic_release_notes_claude_code_feed
generate_anthropic_release_notes_claude_code_feed: check-env  ## Generate RSS feed for Anthropic Claude Code release notes
	python feed_generators/anthropic_release_notes_claude_code.py

.PHONY: generate_openai_research_feed
generate_openai_research_feed: check-env  ## Generate RSS feed for openai/research
	python feed_generators/openai_research_blog.py

.PHONY: generate_ollama_feed
generate_ollama_feed: check-env  ## Generate RSS feed for ollama/blog
	python feed_generators/ollama_blog.py

.PHONY: generate_paulgraham_feed
generate_paulgraham_feed: check-env  ## Generate RSS feed for paulgraham/articles
	python feed_generators/paulgraham_blog.py

#######################
### Manual Testing  ###
######################

.PHONY: test_feed_workflow
test_feed_workflow:  ## Run the .github/workflows/test_feed.yml workflow locally using act
	@if command -v act >/dev/null 2>&1; then \
	  act --container-architecture linux/amd64 -W .github/workflows/test_feed.yml; \
	else \
	  echo 'The `act` tool is not installed. To run GitHub Actions locally, install act: https://github.com/nektos/act'; \
	fi

.PHONY: test_feed_generate
test_feed_generate: check-env  ## Run the test_feed.py script
	@echo 'Running test_feed.py...'
	@python feed_generators/test_feed.py
