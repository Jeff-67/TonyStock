<p align="center">
    <img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-markdown-open.svg" align="center" width="30%">
</p>
<p align="center"><h1 align="center"># TonyStock-懂你Stock</h1></p>
<p align="center">
	<em>Empowering insights, transforming decisions, fueling success.</em>
</p>
<p align="center">
	<!-- local repository, no metadata badges. --></p>
<p align="center">Built with the tools and technologies:</p>
<p align="center">
	<img src="https://img.shields.io/badge/Anthropic-191919.svg?style=default&logo=Anthropic&logoColor=white" alt="Anthropic">
	<img src="https://img.shields.io/badge/Jinja-B41717.svg?style=default&logo=Jinja&logoColor=white" alt="Jinja">
	<img src="https://img.shields.io/badge/Redis-DC382D.svg?style=default&logo=Redis&logoColor=white" alt="Redis">
	<img src="https://img.shields.io/badge/RabbitMQ-FF6600.svg?style=default&logo=RabbitMQ&logoColor=white" alt="RabbitMQ">
	<img src="https://img.shields.io/badge/tqdm-FFC107.svg?style=default&logo=tqdm&logoColor=black" alt="tqdm">
	<img src="https://img.shields.io/badge/MongoDB-47A248.svg?style=default&logo=MongoDB&logoColor=white" alt="MongoDB">
	<img src="https://img.shields.io/badge/Playwright-2EAD33.svg?style=default&logo=Playwright&logoColor=white" alt="Playwright">
	<img src="https://img.shields.io/badge/NumPy-013243.svg?style=default&logo=NumPy&logoColor=white" alt="NumPy">
	<br>
	<img src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=default&logo=Pytest&logoColor=white" alt="Pytest">
	<img src="https://img.shields.io/badge/Docker-2496ED.svg?style=default&logo=Docker&logoColor=white" alt="Docker">
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=default&logo=Python&logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/Poetry-60A5FA.svg?style=default&logo=Poetry&logoColor=white" alt="Poetry">
	<img src="https://img.shields.io/badge/AIOHTTP-2C5BB4.svg?style=default&logo=AIOHTTP&logoColor=white" alt="AIOHTTP">
	<img src="https://img.shields.io/badge/pandas-150458.svg?style=default&logo=pandas&logoColor=white" alt="pandas">
	<img src="https://img.shields.io/badge/OpenAI-412991.svg?style=default&logo=OpenAI&logoColor=white" alt="OpenAI">
	<img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=default&logo=Pydantic&logoColor=white" alt="Pydantic">
</p>
<br>

##  Table of Contents

- [ Overview](#-overview)
- [ Features](#-features)
- [ Project Structure](#-project-structure)
  - [ Project Index](#-project-index)
- [ Getting Started](#-getting-started)
  - [ Prerequisites](#-prerequisites)
  - [ Installation](#-installation)
  - [ Usage](#-usage)
  - [ Testing](#-testing)
- [ Project Roadmap](#-project-roadmap)
- [ Contributing](#-contributing)
- [ License](#-license)
- [ Acknowledgments](#-acknowledgments)

---

##  Overview

TonyStock is a cutting-edge open-source project designed to streamline financial research and analysis. By integrating AI-powered chat agents and search frameworks, TonyStock empowers users to gather valuable insights on companies and industries efficiently. Ideal for investors and analysts, this project enhances decision-making processes and unlocks investment opportunities with ease.

---

##  Features

|      | Feature         | Summary       |
| :--- | :---:           | :---          |
| ⚙️  | **Architecture**  | <ul><li>Utilizes **Flask** server for LINE Bot integration</li><li>Implements **FastAPI** server for chat functionality</li><li>Orchestrates services using **Docker** and **docker-compose.yaml**</li></ul> |
| 🔩 | **Code Quality**  | <ul><li>Follows PEP 8 guidelines for Python code consistency</li><li>Utilizes **Poetry** for managing dependencies</li><li>Includes custom logging with **LoggerFactory** for consistent output</li></ul> |
| 📄 | **Documentation** | <ul><li>Primary language: **Python**</li><li>Package managers: **pip** and **Poetry**</li><li>Contains YAML, TOML, and TXT files for configuration</li></ul> |
| 🔌 | **Integrations**  | <ul><li>Integrates **LINE Messaging API** for user interactions</li><li>Utilizes **Claude AI** for processing user messages</li><li>Combines search and web scraping in research agents</li></ul> |
| 🧩 | **Modularity**    | <ul><li>Separates database operations in **utils.py** for Redis, MongoDB, and MySQL</li><li>Defines system prompts in **prompts** directory for AI assistant</li><li>Utilizes **agents** directory for structured chat agents</li></ul> |
| 🧪 | **Testing**       | <ul><li>Includes test file **test.py** for crawling and cleaning financial news content</li><li>Uses **pytest** for running test suites</li><li>Ensures tool execution verification in **trial_agent.py**</li></ul> |
| ⚡️  | **Performance**   | <ul><li>Optimizes stock-related operations with **stock_utils.py**</li><li>Implements health checks in **docker-compose.yaml** for service reliability</li><li>Utilizes **uvicorn** for starting the FastAPI server</li></ul> |
| 🛡️ | **Security**      | <ul><li>Manages application settings securely in **settings.py**</li><li>Ensures log directory existence in **src/logger.py**</li><li>Follows secure coding practices for handling user messages</li></ul> |
| 📦 | **Dependencies**  | <ul><li>Manages dependencies using **requirements.txt** and **poetry.lock**</li><li>Includes a wide range of dependencies for various functionalities</li><li>Ensures compatibility with Python versions 3.11 and above</li></ul> |

---

##  Project Structure

```sh
└── TonyStock/
    ├── LICENSE
    ├── README.md
    ├── __pycache__
    │   ├── settings.cpython-311.pyc
    │   └── utils.cpython-311.pyc
    ├── agents
    │   ├── __init__.py
    │   ├── __pycache__
    │   ├── research_agents
    │   └── trial_agent.py
    ├── api
    │   ├── __init__.py
    │   └── server.py
    ├── cursor_intelligence
    │   └── cursor_prompt
    ├── docker-compose.yaml
    ├── learning_examples
    │   ├── taiwan_stock
    │   └── us_stock
    ├── logs
    ├── main.py
    ├── poetry.lock
    ├── prompts
    │   ├── 3036_instruction.md
    │   ├── 3413_instruction.md
    │   ├── 8299_instruction.md
    │   ├── __init__.py
    │   ├── __pycache__
    │   ├── analysis_prompts.py
    │   ├── system_prompts.md
    │   └── system_prompts.py
    ├── pyproject.toml
    ├── requirements.txt
    ├── settings.py
    ├── src
    │   ├── __init__.py
    │   └── logger.py
    ├── static
    │   ├── .DS_Store
    │   └── TSE_ticker.csv
    ├── test.py
    ├── tests
    │   ├── __init__.py
    │   ├── test_financial_data.py
    │   ├── test_llm_api.py
    │   ├── test_market_data.py
    │   ├── test_online_research_agents.py
    │   ├── test_search_engine.py
    │   ├── test_trial_agent.py
    │   └── test_web_scraper.py
    ├── tools
    │   ├── __init__.py
    │   ├── __pycache__
    │   ├── financial_data
    │   ├── financial_data_fetcher.py
    │   ├── llm_api.py
    │   ├── market_data_fetcher.py
    │   ├── read_pdf.py
    │   ├── search_engine.py
    │   ├── time_tool.py
    │   └── web_scraper.py
    ├── utils
    │   ├── __init__.py
    │   └── stock_utils.py
    └── utils.py
```


###  Project Index
<details open>
	<summary><b><code>TONYSTOCK/</code></b></summary>
	<details> <!-- __root__ Submodule -->
		<summary><b>__root__</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/docker-compose.yaml'>docker-compose.yaml</a></b></td>
				<td>- Orchestrates Docker services for MongoDB, MySQL, RabbitMQ, and Redis<br>- Defines environment variables, volumes, ports, and health checks for each service<br>- Ensures seamless communication and data storage across containers.</td>
			</tr>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/requirements.txt'>requirements.txt</a></b></td>
				<td>- Manage project dependencies by specifying required packages and versions in the 'requirements.txt' file<br>- Ensure compatibility with Python versions 3.11 and above, while considering platform-specific dependencies<br>- This file plays a crucial role in maintaining a stable and functional codebase by defining the necessary external libraries for the project.</td>
			</tr>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/pyproject.toml'>pyproject.toml</a></b></td>
				<td>Manages project dependencies and build configuration using Poetry in the codebase architecture.</td>
			</tr>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/test.py'>test.py</a></b></td>
				<td>- Crawl and clean financial news content from web sources using a module in the codebase<br>- The module removes messy hyperlinks and formatting from markdown text, ensuring clean content for analysis<br>- The code integrates a web crawler to fetch content and a cleaning function to process the retrieved data.</td>
			</tr>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/logs'>logs</a></b></td>
				<td>Log user interactions and system events for monitoring and analysis within the project architecture.</td>
			</tr>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/utils.py'>utils.py</a></b></td>
				<td>- Manages connections and operations for Redis, MongoDB, and MySQL databases, facilitating data caching, insertion, and retrieval<br>- Implements methods for interacting with each database type, ensuring seamless data handling and storage<br>- The code file serves as a central hub for database management within the project architecture.</td>
			</tr>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/settings.py'>settings.py</a></b></td>
				<td>- Define application settings, including log level, environment, and various configurations for Redis, MongoDB, and MySQL<br>- Set OPIK URL override based on the environment.</td>
			</tr>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/main.py'>main.py</a></b></td>
				<td>- Implements a Flask server for a LINE Bot that processes user messages using Claude AI and responds via the LINE Messaging API<br>- Handles webhook events, validates signatures, and sends appropriate responses back to users.</td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- cursor_intelligence Submodule -->
		<summary><b>cursor_intelligence</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/cursor_intelligence/cursor_prompt'>cursor_prompt</a></b></td>
				<td>- The code file in `cursor_intelligence/cursor_prompt` is responsible for configuring the top-level settings for the AI coding assistant powered by GPT-4o within the Cursor IDE<br>- It defines the model, temperature, and user information for the assistant, setting the stage for pair programming with a user to solve coding tasks<br>- This file plays a crucial role in initializing the AI assistant and facilitating collaborative coding sessions within the Cursor IDE.</td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- agents Submodule -->
		<summary><b>agents</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/agents/trial_agent.py'>trial_agent.py</a></b></td>
				<td>- The code file `trial_agent.py` implements a chat agent that interacts with the Claude AI model, processes responses, executes tools based on model requests, and verifies tool execution results<br>- It provides a structured approach to handling conversations with tool usage capabilities within the project architecture.</td>
			</tr>
			</table>
			<details>
				<summary><b>research_agents</b></summary>
				<blockquote>
					<table>
					<tr>
						<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/agents/research_agents/onlin_research_agents.py'>onlin_research_agents.py</a></b></td>
						<td>- Combines search and web scraping to retrieve and structure content from URLs<br>- Provides a unified interface for searching and scraping, returning results in a structured JSON format<br>- The code integrates search engine functionality to retrieve URLs, scrapes content from those URLs, and combines search results with scraped content.</td>
					</tr>
					<tr>
						<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/agents/research_agents/search_framework_agent.py'>search_framework_agent.py</a></b></td>
						<td>- Generates comprehensive company research queries by utilizing LLM to analyze industry characteristics, competitive advantages, and value chain<br>- Implements the initial step of the analysis framework, providing structured search queries based on the company's profile.</td>
					</tr>
					</table>
				</blockquote>
			</details>
		</blockquote>
	</details>
	<details> <!-- utils Submodule -->
		<summary><b>utils</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/utils/stock_utils.py'>stock_utils.py</a></b></td>
				<td>- Provides utility functions for stock-related operations, including mapping stock names to IDs and parsing messages<br>- Enables retrieval of stock names from user messages, enhancing the system's stock-related functionalities within the codebase architecture.</td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- prompts Submodule -->
		<summary><b>prompts</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/prompts/system_prompts.py'>system_prompts.py</a></b></td>
				<td>- SUMMARY:
The `system_prompts.py` file in the project serves as the system prompts module for an AI financial research assistant<br>- It provides base system prompts, tool configurations, and specialized finance agent prompts<br>- The `system_prompt` function generates a formatted system prompt for the assistant, incorporating the model name and complete instructions<br>- The file plays a crucial role in enhancing user interaction and guiding users through the financial research process within the AI assistant.</td>
			</tr>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/prompts/analysis_prompts.py'>analysis_prompts.py</a></b></td>
				<td>- Generate prompts for search framework analysis based on company-specific context and industry characteristics, guiding users to identify key areas, strengths/weaknesses, opportunities/threats, and more<br>- Encourage the creation of a JSON array of search queries with specific formats for query, purpose, and expected insights<br>- Incorporate company identifiers and keywords to gain valuable insights for investment opportunities.</td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- api Submodule -->
		<summary><b>api</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/api/server.py'>server.py</a></b></td>
				<td>- Implements a FastAPI server exposing a chat endpoint for interacting with TonyStock's chat functionality<br>- Handles user messages using chat_with_claude and provides a health check endpoint<br>- The server starts using uvicorn, ensuring seamless communication with the chat API.</td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- src Submodule -->
		<summary><b>src</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='/Users/shou/Desktop/AI_project/TonyStock/blob/master/src/logger.py'>logger.py</a></b></td>
				<td>- Implements custom logging formatters and handlers for consistent, colored output and file logging support<br>- LoggerFactory creates configured logger instances with specified formatters and handlers<br>- FileHandler ensures log directory existence, while ConsoleHandler outputs logs to the console.</td>
			</tr>
			</table>
		</blockquote>
	</details>
</details>

---
##  Getting Started

###  Prerequisites

Before getting started with TonyStock, ensure your runtime environment meets the following requirements:

- **Programming Language:** Python
- **Package Manager:** Pip, Poetry
- **Container Runtime:** Docker


###  Installation

Install TonyStock using one of the following methods:

**Build from source:**

1. Clone the TonyStock repository:
```sh
❯ git clone ../TonyStock
```

2. Navigate to the project directory:
```sh
❯ cd TonyStock
```

3. Install the project dependencies:


**Using `pip`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white" />](https://pypi.org/project/pip/)

```sh
❯ pip install -r requirements.txt
```


**Using `poetry`** &nbsp; [<img align="center" src="https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json" />](https://python-poetry.org/)

```sh
❯ poetry install
```


**Using `docker`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Docker-2CA5E0.svg?style={badge_style}&logo=docker&logoColor=white" />](https://www.docker.com/)

```sh
❯ docker build -t AI_project/TonyStock .
```




###  Usage
Run TonyStock using the following command:
**Using `pip`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white" />](https://pypi.org/project/pip/)

```sh
❯ python {entrypoint}
```


**Using `poetry`** &nbsp; [<img align="center" src="https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json" />](https://python-poetry.org/)

```sh
❯ poetry run python {entrypoint}
```


**Using `docker`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Docker-2CA5E0.svg?style={badge_style}&logo=docker&logoColor=white" />](https://www.docker.com/)

```sh
❯ docker run -it {image_name}
```


###  Testing
Run the test suite using the following command:
**Using `pip`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white" />](https://pypi.org/project/pip/)

```sh
❯ pytest
```


**Using `poetry`** &nbsp; [<img align="center" src="https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json" />](https://python-poetry.org/)

```sh
❯ poetry run pytest
```


---
##  Project Roadmap

- [X] **`Task 1`**: <strike>Implement feature one.</strike>
- [ ] **`Task 2`**: Implement feature two.
- [ ] **`Task 3`**: Implement feature three.

---

##  Contributing

- **💬 [Join the Discussions](https://LOCAL/AI_project/TonyStock/discussions)**: Share your insights, provide feedback, or ask questions.
- **🐛 [Report Issues](https://LOCAL/AI_project/TonyStock/issues)**: Submit bugs found or log feature requests for the `TonyStock` project.
- **💡 [Submit Pull Requests](https://LOCAL/AI_project/TonyStock/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your LOCAL account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone /Users/shou/Desktop/AI_project/TonyStock
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to LOCAL**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="left">
   <a href="https://LOCAL{/AI_project/TonyStock/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=AI_project/TonyStock">
   </a>
</p>
</details>

---

##  License

This project is protected under the [SELECT-A-LICENSE](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

##  Acknowledgments

- List any resources, contributors, inspiration, etc. here.

---
