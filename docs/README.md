# WikiLLM

WikiLLM is an interactive project that combines quizzes and courses to enhance your learning experience. With WikiLLM, you can test your knowledge through AI-generated quizzes, dive into structured courses, receive detailed explanations and hints, and even simulate real exam scenarios like the Brevet Blanc.

## Features

- **Interactive Quizzes**: Enjoy dynamically generated quizzes with modes such as speed test and normal. Track answer times, review detailed feedback, and improve your performance.
- **Detailed Explanations & Hints**: After each question, access in-depth explanations and use hints to better understand the content.
- **Course Content**: Access comprehensive, structured courses across various subjects.
- **Brevet Blanc Simulation**: Simulate the French Brevet exam with progress-based quizzes and detailed performance results.
- **User Metrics**: Monitor your performance with metrics like average answer time, success rates, and more.
- **Administrative Dashboard**: Administrators can view aggregated data, manage quizzes, and analyze performance trends.

## Installation

Ensure you have [Python 3.10](https://www.python.org/downloads/release/python-310/) installed. Then follow these steps to set up your environment:

```bash
# Create a new Conda environment
conda create -n wikillm python==3.10

# Activate the environment
conda activate wikillm

# Navigate to the project directory
cd wikillm

# Install dependencies
pip install -r requirements.txt
```

## Configuration

 Create a `.env` file in the project root and add the necessary environment variables (e.g., your MISTRAL_API_KEY):

   ```
   MISTRAL_API_KEY=your_mistral_api_key_here
   ```



## Usage

To launch the application, run:

```bash
streamlit run app.py
```

This command will start the WikiLLM application. Use the sidebar for navigation between the main dashboard, the admin panel, and the Brevet Blanc simulation.

## Project Structure

```
.env
.gitignore
.streamlit/
    config.toml
app.py
docs/
    README.md
    memo.txt
pages/
    admin.py
    brevet.py
    ressources/
        components.py
requirements.txt
src/
    db/
        utils.py
    metrics_database.py
    ml_model.py
    rag.py
    digischool.ipynb
    schoolmove.ipynb
    scrapper.py
```

- **app.py**: Main application entry point.
- **pages/**: Contains additional pages such as the admin dashboard and Brevet Blanc.
- **pages/ressources/components.py**: Contains UI components, dialogs, and navigation elements.
- **src/**: Core logic including database utilities, metrics, model handling, and data scraping.
- **docs/**: Documentation and related project files.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements or bug fixes. Refer to the [GitHub Flow](https://guides.github.com/introduction/flow/) for branch management guidelines.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for further details.

## Contact

For any questions or support, feel free to reach out to the maintainers:

- [Alexis GABRYSCH](https://github.com/AlexisGabrysch)
- [Antoine ORUEZABALA](https://github.com/AntoineORUEZABALA)
- [Lucile PERBET](https://github.com/lucilecpp)
- [Alexis DARDELET](https://github.com/AlexisDardelet)

Visit the project repository on [GitHub](https://github.com/AlexisGabrysch/wikillm).